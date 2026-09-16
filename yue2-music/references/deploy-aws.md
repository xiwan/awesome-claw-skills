# 在 AWS 上部署 YuE2 后端

从零起一台能跑 YuE2 的 GPU 机器，用 SSM 驱动，不开任何入站端口。
下面所有 `<占位符>` 都要替换成你自己的值。

这份笔记记录的是一次真实部署踩过的坑，不是理想路径。

---

## 1. 显存：官方数字比实测保守很多

上游文档写的是「BF16-capable NVIDIA GPU with 24 GB VRAM」。这个数字指的是**显卡的标称规格**，
不是实测占用。容易被误读成"24GB 卡刚好不够"——因为 `nvidia-smi` 报一张标称 24GB 的卡是
23034 MiB（GB 与 GiB 的换算差），看起来像是不达标。它是达标的。

一次 59 秒歌曲的**实测峰值只有 8500 MiB**：

| 阶段 | 显存 |
|------|------|
| 加载模型 | ~7.8 GB |
| 符号规划 + 语义生成 | ~8.4 GB |
| flow matching + VAE 解码 | **8.5 GB 峰值** |

所以 24GB 档的卡对一分钟的歌有 2.5 倍余量。**但自回归部分的 KV cache 随歌长增长**，
整首歌（3–4 分钟）的峰值要自己重测，不要拿这个数字当全长曲目的结论。

| 实例 | GPU | 显存 | vCPU/内存 | 说明 |
|------|-----|------|-----------|------|
| `g6.xlarge` | L4 | 24GB | 4 / 16GB | 一分钟级片段够用，最省 |
| `g5.2xlarge` | A10G | 24GB | 8 / 32GB | 显存带宽 600GB/s，比 L4 的 300GB/s 快 |
| `g6.4xlarge` | L4 | 24GB | 16 / 64GB | CPU/内存宽裕 |
| `g6e.xlarge` | L40S | 48GB | 4 / 32GB | 长曲目留余量 |

不做量化，所以没有靠 int8/int4 压到小显存的官方路径。

## 2. 容量：别逐个 AZ 试

热门 GPU 机型经常整个区域缺货，而且各 AZ 返回的报错会互相矛盾——A 说"试 B/C/D"，
换到 B 又说"试 A/C/D"。逐个 `run-instances` 纯属浪费时间。用
`create-fleet --type instant` 一次调用铺开全部「机型 × AZ」组合：

```bash
aws ec2 create-launch-template --launch-template-name <yue2-lt> \
  --launch-template-data file://lt-data.json

cat > fleet.json <<'EOF'
{
  "LaunchTemplateConfigs": [{
    "LaunchTemplateSpecification": { "LaunchTemplateName": "<yue2-lt>", "Version": "$Latest" },
    "Overrides": [
      { "InstanceType": "g6e.xlarge",  "SubnetId": "<subnet-a>", "Priority": 1 },
      { "InstanceType": "g6e.xlarge",  "SubnetId": "<subnet-b>", "Priority": 1 },
      { "InstanceType": "g5.2xlarge",  "SubnetId": "<subnet-a>", "Priority": 2 },
      { "InstanceType": "g6.4xlarge",  "SubnetId": "<subnet-a>", "Priority": 3 },
      { "InstanceType": "g6.xlarge",   "SubnetId": "<subnet-a>", "Priority": 4 },
      { "InstanceType": "g6.xlarge",   "SubnetId": "<subnet-b>", "Priority": 4 }
    ]
  }],
  "TargetCapacitySpecification": { "TotalTargetCapacity": 1, "DefaultTargetCapacityType": "on-demand" },
  "OnDemandOptions": { "AllocationStrategy": "prioritized" },
  "Type": "instant"
}
EOF

aws ec2 create-fleet --cli-input-json file://fleet.json
```

Spot 是**独立的容量池**，按需缺货时值得一并试；生成任务只有几分钟，被回收的代价很低。

## 3. AMI：直接用 Deep Learning Base

选 **Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)**。驱动和 CUDA 都是现成的，
不用自己装：

```bash
aws ssm get-parameters-by-path --output text \
  --path /aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04 \
  --query 'Parameters[].Name' | tr '\t' '\n' | tail -5
```

## 4. bootstrap：Ubuntu 22.04 自带的 Python 是 3.10

上游要求 Python 3.12（`pyproject.toml` 写的是 `>=3.10`，但文档和支持基线是 3.12）。
deadsnakes PPA 只**新增** `/usr/bin/python3.12`，不改 `python3` 的指向，所以不会破坏系统或
同机上其他服务的 venv。

写成 launch template 的 user-data：

```bash
#!/bin/bash
set -xeuo pipefail
exec > >(tee -a /var/log/yue2-bootstrap.log) 2>&1

export DEBIAN_FRONTEND=noninteractive
YUE_DIR=/opt/yue2
YUE_USER=ubuntu
export HF_HOME="$YUE_DIR/hf-cache"

apt-get update -y
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y python3.12 python3.12-venv python3.12-dev git ffmpeg libsndfile1 jq

git clone --depth 1 https://github.com/multimodal-art-projection/YuE.git "$YUE_DIR/YuE"
cd "$YUE_DIR/YuE"
git rev-parse HEAD > "$YUE_DIR/YuE.commit"       # 记下 revision，便于复现

python3.12 -m venv "$YUE_DIR/venv"
source "$YUE_DIR/venv/bin/activate"
pip install --upgrade pip wheel setuptools
pip install .                                    # 会固定 torch==2.10.0
pip install "huggingface_hub[hf_transfer]" hf_transfer

# 预热权重，省掉首次生成时的等待
mkdir -p "$HF_HOME"
export HF_HUB_ENABLE_HF_TRANSFER=1
hf download m-a-p/YuE2-3B  || huggingface-cli download m-a-p/YuE2-3B
hf download m-a-p/YuE2-Vae || huggingface-cli download m-a-p/YuE2-Vae

cat > /etc/profile.d/yue2.sh <<EOF
export HF_HOME=$YUE_DIR/hf-cache
export HF_HUB_ENABLE_HF_TRANSFER=1
export PATH=$YUE_DIR/venv/bin:\$PATH
EOF

mkdir -p "$YUE_DIR/work"
chown -R "$YUE_USER":"$YUE_USER" "$YUE_DIR"
touch /var/log/yue2-bootstrap.DONE               # 哨兵，便于判断是否装完
```

整个过程约 6 分钟，权重约 7.3 GB。磁盘给 150GB 起（DLAMI 本身占 70GB 左右）。
EBS 记得开加密——不花钱，没副作用。

**没有 systemd service。** YuE2 是库和 CLI，没有常驻进程。只有你自己在前面套了
Web UI（Gradio 之类）才需要写 unit。

## 5. 接入：SSM，零入站

```bash
# 角色只需要 SSM core
aws iam create-role --role-name <yue2-role> \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
    "Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name <yue2-role> \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

# 回传产物用的最小 S3 权限（限定到你自己的桶）
aws iam put-role-policy --role-name <yue2-role> --policy-name yue2-s3-outputs \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
    "Action":["s3:PutObject","s3:AbortMultipartUpload"],
    "Resource":"arn:aws:s3:::<your-bucket>/*"}]}'

aws iam create-instance-profile --instance-profile-name <yue2-profile>
aws iam add-role-to-instance-profile --instance-profile-name <yue2-profile> \
  --role-name <yue2-role>

# 安全组：入站一条都不要，SSM 走出站
aws ec2 create-security-group --group-name <yue2-sg> \
  --description "YuE2 GPU host - no inbound, SSM only" --vpc-id <vpc-id>
```

不设 key pair，不开 22 端口。launch template 里把 `MetadataOptions.HttpTokens` 设成
`required`（强制 IMDSv2）。

产物回传走 S3 是因为 SSM 命令输出有大小上限，装不下音频。桶要私有、开 SSE、加生命周期
过期规则。

## 6. 成本

一分钟的歌大约消耗一分钟 GPU 时间，所以**按需 + 用完即停**比常开划算得多。
`scripts/remote.sh start` / `stop` 就是干这个的。

停机后 EBS 保留，但**下次 `start` 的容量不保证**——热门机型可能起不来。长期要稳定
可用就考虑 Capacity Reservation。

## 7. 踩坑清单

| 现象 | 原因 |
|------|------|
| 所有 AWS 调用 `AuthFailure` / `InvalidClientTokenId` | 环境变量里的过期 token 遮挡了 `~/.aws/credentials`。设 `YUE2_CLEAR_ENV_CREDS=1` |
| `InsufficientInstanceCapacity` 反复出现且各 AZ 建议互相矛盾 | 区域级缺货。改用 `create-fleet --type instant`，别循环 `run-instances` |
| `run-instances` 报 `Network interfaces and an instance-level subnet ID may not be specified on the same request` | launch template 里写了 `NetworkInterfaces`，就不能再传 `--subnet-id`。改成顶层 `SecurityGroupIds`，子网留到运行时传 |
| `pip install .` 后 `torch.cuda.is_available()` 为 False | 用了非 DLAMI 的镜像，缺驱动 |
| ABC 编辑被 `abc_tools.py` 拒绝 | 原生和弦词表只有 `major, m, dim, aug, 7, maj7, m7, dim7, m7b5, sus4, sus2, 6, m6, 7sus4, m(maj7)`。`Cmaj9` / `C13` / `A7alt` 不支持，复杂 voicing 要写进 style prompt |
| 生成中途 SSM 命令超时 | 用 `nohup ... &` 让任务脱离该次调用，再轮询 `result.json` |
