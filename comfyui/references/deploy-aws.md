# 在 AWS 上部署 ComfyUI 后端

从零起一台给这个 skill 用的 GPU 后端。下面所有 `<占位符>` 都要替换成你自己的值。

这份笔记记录的是一次真实部署踩过的坑，不是理想路径。

---

## 1. 选机型：先算显存

**先按显存筛，再谈价格。** 装不进显存的模型要靠 CPU offload，慢到没有实用价值。

| 模型 | 参数量 | 最省显存的可用形态 | 24GB 卡 |
|------|--------|--------------------|---------|
| SD 1.5 / SDXL | 1–3B | fp16 | 富余 |
| FLUX.1 dev/schnell | 12B | fp8 all-in-one ≈ 17GB | 舒服 |
| Z-Image Turbo | 6B | bf16 ≈ 12GB + 7.5GB 文本编码器 | 舒服 |
| FLUX.2 dev | 32B | Q4 GGUF ≈ 19GB **+** Mistral-24B 编码器 fp8 ≈ 12.5GB | **装不进** |

FLUX.2 需要 48GB 级别（`g6e.*` / L40S）。24GB 卡上跑它要反复 offload，不值得。

| 实例 | GPU | 显存 | 内存 | 说明 |
|------|-----|------|------|------|
| `g5.2xlarge` | A10G | 24GB | 32GB | 24GB 档性价比首选 |
| `g6.2xlarge` | L4 | 24GB | 32GB | 更新，但显存带宽仅 300GB/s（A10G 600GB/s），出图更慢 |
| `g6.4xlarge` | L4 | 24GB | 64GB | 同上，CPU/内存更多 |
| `g6e.2xlarge` | L40S | 48GB | 64GB | 能跑 FLUX.2 |

**A10G 比 L4 快**，尽管 L4 更新——扩散推理吃显存带宽。

### 容量：别逐个 AZ 试

热门 GPU 机型经常整个区域缺货，且各 AZ 的报错信息会互相矛盾。逐个
`run-instances` 试是浪费时间。用 `create-fleet --type instant` 一次调用覆盖
全部「机型 × AZ」组合，让 EC2 自己找：

```bash
# 先建启动模板（含 user-data、EBS、SG、IAM 等）
aws ec2 create-launch-template --launch-template-name comfyui-lt \
  --launch-template-data file://lt-data.json

# 再用 fleet 一次性铺开所有候选，prioritized 表示按 Priority 从小到大优先
cat > fleet.json <<'EOF'
{
  "LaunchTemplateConfigs": [{
    "LaunchTemplateSpecification": {"LaunchTemplateName": "comfyui-lt", "Version": "1"},
    "Overrides": [
      {"InstanceType": "g5.2xlarge",  "SubnetId": "<subnet-a>", "Priority": 1.0},
      {"InstanceType": "g5.2xlarge",  "SubnetId": "<subnet-b>", "Priority": 2.0},
      {"InstanceType": "g5.2xlarge",  "SubnetId": "<subnet-c>", "Priority": 3.0},
      {"InstanceType": "g6e.2xlarge", "SubnetId": "<subnet-a>", "Priority": 4.0},
      {"InstanceType": "g6.4xlarge",  "SubnetId": "<subnet-a>", "Priority": 5.0}
    ]
  }],
  "TargetCapacitySpecification": {
    "TotalTargetCapacity": 1, "OnDemandTargetCapacity": 1,
    "DefaultTargetCapacityType": "on-demand"
  },
  "OnDemandOptions": {"AllocationStrategy": "prioritized"},
  "Type": "instant"
}
EOF
aws ec2 create-fleet --cli-input-json file://fleet.json
```

返回里 `Instances` 是成功的，`Errors` 列出每个失败组合的原因。

### AMI 与磁盘

用 Deep Learning Base OSS Nvidia Driver AMI（已带驱动和 CUDA，不带 PyTorch）：

```bash
aws ssm get-parameters-by-path --region <region> \
  --path /aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04/latest \
  --query 'Parameters[].Value' --output text
```

磁盘按模型体积估：FLUX.1 两个 fp8 各 17GB、Z-Image Turbo 一套约 20GB、PyTorch 约 5GB。
**250GB gp3 起步**，并显式打开加密（账户默认加密往往是关的）：

```json
"BlockDeviceMappings": [{
  "DeviceName": "/dev/sda1",
  "Ebs": {"VolumeSize": 250, "VolumeType": "gp3", "Iops": 6000,
          "Throughput": 500, "Encrypted": true, "DeleteOnTermination": true}
}]
```

> `Encrypted: true` 很容易漏。卷建完**无法原地加密**，只能快照重建。

---

## 2. 安装（user-data）

```bash
#!/bin/bash
set -xeuo pipefail
apt-get update -y && apt-get install -y git python3-venv python3-pip

git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI
cd /opt/ComfyUI
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip wheel
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements.txt
pip install "huggingface_hub[hf_transfer]"

export HF_HUB_ENABLE_HF_TRANSFER=1
# FLUX.1 fp8 all-in-one（含 UNet + CLIP-L + T5-XXL + VAE，单文件即可用）
hf download Comfy-Org/flux1-schnell flux1-schnell-fp8.safetensors --local-dir models/checkpoints
# Z-Image Turbo（分离式，三个文件分别放不同目录）
hf download Comfy-Org/z_image_turbo split_files/diffusion_models/z_image_turbo_bf16.safetensors --local-dir /tmp/zi
hf download Comfy-Org/z_image_turbo split_files/text_encoders/qwen_3_4b.safetensors --local-dir /tmp/zi
hf download Comfy-Org/z_image_turbo split_files/vae/ae.safetensors --local-dir /tmp/zi
mv /tmp/zi/split_files/diffusion_models/* models/diffusion_models/
mv /tmp/zi/split_files/text_encoders/*   models/text_encoders/
mv /tmp/zi/split_files/vae/*             models/vae/
chown -R ubuntu:ubuntu /opt/ComfyUI

cat > /etc/systemd/system/comfyui.service <<'EOF'
[Unit]
Description=ComfyUI
After=network-online.target
[Service]
User=ubuntu
WorkingDirectory=/opt/ComfyUI
ExecStart=/opt/ComfyUI/venv/bin/python main.py --listen 0.0.0.0 --port 8188
Restart=always
[Install]
WantedBy=multi-user.target
EOF
systemctl enable --now comfyui
```

> ComfyUI 自带的默认启动工作流引用 Z-Image Turbo 那三个文件。装上它们，
> Web 界面打开就能直接跑；不装则首屏会显示 `2 errors found` 红色横幅。

---

## 3. 别把 ComfyUI 直接暴露在公网

**ComfyUI 没有任何认证机制**，而它能通过 ComfyUI-Manager 安装任意 custom node，
等价于**任意代码执行**。裸暴露 8188 相当于把 shell 交出去。

安全组：8188 只允许来自负载均衡器的安全组，不写 CIDR：

```bash
aws ec2 authorize-security-group-ingress --group-id <ec2-sg> \
  --ip-permissions 'IpProtocol=tcp,FromPort=8188,ToPort=8188,UserIdGroupPairs=[{GroupId=<alb-sg>}]'
```

运维走 SSM Session Manager，不开 SSH（实例挂 `AmazonSSMManagedInstanceCore` 角色即可）。

### 两条访问路径

**浏览器 → ALB + Cognito。** ALB 的 HTTPS 监听器默认动作设成
`authenticate-cognito`(Order 1) + `forward`(Order 2)。需要 ACM 证书，
因此需要一个**真实委派到 Route53 的域名**。

> 踩过的坑：Route53 里存在托管区 ≠ 域名已委派。先确认
> `dig <your-domain> NS` 有返回，否则 ACM 的 DNS 验证永远 pending。

**脚本 / API → 请求头密钥。** ALB Cognito 是给浏览器重定向设计的，CLI 用不了。
加一条优先级更高的监听器规则，匹配自定义请求头就直接放行：

```bash
KEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(32))")
aws elbv2 create-rule --listener-arn <https-listener-arn> --priority 1 \
  --conditions "Field=http-header,HttpHeaderConfig={HttpHeaderName=X-Comfy-Key,Values=[$KEY]}" \
  --actions "Type=forward,TargetGroupArn=<target-group-arn>"
```

把 `KEY` 填进 `secrets/comfyui.env` 的 `COMFY_API_KEY`。要吊销就删这条规则。
验证行为应为：正确 key → 200，无 key 或错 key → 302（重定向到登录页）。

---

## 4. 反代后的两个坑

**Cognito 登录跳回来时 403。** ComfyUI 的 CSRF 防护会拒绝跨站请求：

```python
if request.headers.get('Sec-Fetch-Site') == 'cross-site':
    return web.Response(status=403)
```

从 Cognito 域跳回你的域，这次顶层导航带的正是 `Sec-Fetch-Site: cross-site`。
两个解法：

1. 给 ComfyUI 加 `--enable-cors-header https://<your-domain>`（**传具体域名，不要用 `*`**）。
   这会整体替换掉那个中间件，`cross-site` 检查随之消失。
2. 更干净：给 Cognito 配一个**与应用同父域**的自定义域名（如 `auth.example.com`
   对 `comfy.example.com`），跳转就变成 `same-site`，ComfyUI 放行，无需削弱防护。

注意该分支 `return` 前**不写日志**，所以 ComfyUI 日志里看不到任何 403 记录，很难查。

**Web 界面在高延迟链路上极慢。** ComfyUI 首屏约 64 个文件、1.78MB，且：

- 静态资源的响应头是 `Cache-Control: no-store` —— 连带哈希命名的不可变资源也不许缓存，**每次刷新全量重下**
- `--enable-compress-response-body` **只压 `application/json` 和 `text/plain`**，JS/CSS 一律跳过，静态文件走 `FileResponse` 连第一个 isinstance 检查都过不了
- HTTP/2 单连接，链路丢包时 TCP 队头阻塞会卡住所有并发流

实测 200ms RTT + 丢包的链路上，有效吞吐仅约 20KB/s，首屏约 90 秒，中途刷新则前功尽弃。

**这就是本 skill 存在的理由**——API 只有几 KB JSON 往返，加上 `preview=webp` 服务端转码，
取图从 1.2MB 降到 116KB。想改善 Web 界面则需要在前面加 nginx（改写 Cache-Control + gzip）
或 CloudFront（额外获得 HTTP/3，从协议层消除队头阻塞）。

---

## 5. 成本

| 项 | 参考 |
|----|------|
| `g5.2xlarge` / `g6.4xlarge` | ≈ $1.2–1.4 /小时（约 $30 /天不停机） |
| gp3 250GB | ≈ $20 /月，**停机仍计费** |
| ALB | ≈ $16 /月 + LCU |

**停机只停计算，不停磁盘。** 用 `scripts/instance.sh stop`。
长期不用可连 ALB 一起删，Cognito 用户池和 ACM 证书留着，重建很快。

---

## 6. 部署完的安全自查

容易漏的几项：

- [ ] EBS 卷加密（`Encrypted: true`，**建完无法补加**）
- [ ] Cognito 开启 MFA
- [ ] 实例放私有子网 + NAT / VPC Endpoint，而非公有子网带公网 IP
- [ ] ALB 访问日志开启（排障时是唯一的真相来源）
- [ ] ALB → 实例段加密（ComfyUI 不支持 TLS，需 nginx 终结）
- [ ] 安全组出站收紧（默认 `0.0.0.0/0` 全开）
- [ ] API 密钥进密钥管理，而非明文文件
- [ ] ALB 前面挂 WAF（限速 + 常见攻击特征）

单人实验环境可以接受其中一部分风险，但**要放真实数据前必须补齐**。
