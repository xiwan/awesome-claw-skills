---
name: game-design-coach
description: 'Game design coach — guide users from a one-line idea to a high-quality OpenGame prompt step by step. Trigger when user says "design a game", "game idea", "help me think of a game", "game design", "refine prompt", etc.'
---

# Game Design Coach — OpenGame Prompt Builder

Turn a vague one-sentence game idea into a high-quality, structured prompt ready for OpenGame.

## Why This Exists

OpenGame's output quality depends heavily on prompt quality. A good prompt must cover 6 dimensions:
1. **Core mechanics** (specific interaction rules, not "make a fun game")
2. **Game type / physics model** (determines which OpenGame template module is used)
3. **Visual style** (pixel art, neon, hand-drawn, realistic 16-bit, etc.)
4. **Characters & enemies** (abilities, AI behavior, boss mechanics)
5. **Level/content structure** (how many levels, difficulty curve, scene variety)
6. **UI & feedback** (health bars, score, effects, screen shake)

## Guidance Flow

**Principles:**
- Every question provides concrete options — user picks, not invents
- User says "not sure" / "you decide" / "whatever" → use recommended default, move on
- Never ask more than 3 questions in a row — if user clearly has no preference, fast-track to Step 5 with defaults
- Showing a complete prompt in Step 6 for review is more efficient than agonizing over each question

### Step 1: Classify

Determine the physics model from user's description and confirm:

| Module | Criteria | Examples |
|--------|----------|----------|
| platformer | Character falls, gravity exists | Mario, Street Fighter, Terraria |
| top_down | Free movement, top-down view | Zelda, Vampire Survivors |
| grid_logic | Grid movement, turn-based | Sokoban, Fire Emblem, Match-3 |
| tower_defense | Fixed paths, enemy waves | Kingdom Rush, Bloons TD |
| ui_heavy | Primarily UI interaction | Card games, Visual Novels |

**Output**: "Your game sounds like a [type] — correct?"

### Step 2: Core Mechanics (Most Critical)

**Rule: Every question must offer 2-3 concrete options + a recommended default. User just says "pick A" or "you decide".**

If user says "not sure" / "you decide" / "whatever" → adopt the recommended default and continue. Do not repeatedly ask.

Present 2-3 multiple-choice questions based on confirmed type:

**platformer:**

Q1: Combat style?
- A) Melee combo (punch/kick chains, like Street Fighter) ← recommended, great feel
- B) Ranged shooting (guns/magic projectiles, like Contra)
- C) Hybrid (melee + ranged switching)

Q2: Ultimate/special skill?
- A) Yes! Dash attack ← recommended, simple and flashy
- B) Yes! Screen-clearing AOE
- C) No, keep it simple

Q3: Boss fight?
- A) Yes, final level boss with multi-phase transformation ← recommended
- B) Mini-boss every level
- C) No boss, pure platforming

**top_down:**

Q1: Game pace?
- A) Survival — waves of enemies, survive as long as possible (like Vampire Survivors) ← recommended
- B) Exploration — room-by-room dungeon crawl (like Zelda)

Q2: Weapon?
- A) Melee sword/blade ← recommended, feels great in top-down
- B) Ranged bow/gun
- C) Multiple weapons, switchable

Q3: Progression?
- A) Yes, level-up and pick skills (Roguelike style) ← recommended
- B) No, pure skill-based

**tower_defense:**

Q1: Tower theme? Just give me a keyword, I'll design 3 towers.
- Examples: cats, medieval, sci-fi, plants, food...
- Default: I'll design 3 classic towers (single-target DPS / AOE splash / slow/control)

Q2: How many waves?
- A) 5 waves (short session, casual) ← recommended
- B) 10 waves (medium length)
- C) Endless mode

**grid_logic:**

Q1: Core mechanic?
- A) Push/slide puzzle (strategic thinking) ← recommended
- B) Match-3 / chain reaction (satisfying combos)
- C) Tactical grid combat (move units, attack)

Q2: Level count?
- A) 5 levels, progressive difficulty ← recommended
- B) 10+ levels
- C) Randomly generated

**ui_heavy:**

Q1: Core loop?
- A) Card battle (play cards to fight) ← recommended
- B) Trivia / quiz
- C) Visual novel (branching choices)

Q2: Numeric combat (HP, attack power)?
- A) Yes, defeat opponent to win ← recommended
- B) No, pure narrative / pure quiz

### Step 3: Visuals & Atmosphere

Provide options, not open questions:

"Pick a visual style (or describe your own):"
- A) 90s arcade pixel art (hardcore, nostalgic) ← recommended for action games
- B) Cute hand-drawn Kawaii (pastel, rounded) ← recommended for casual games
- C) Neon cyberpunk (dark background + fluorescent colors)
- D) Gothic dark fantasy (moody, atmospheric)
- E) Minimalist geometric (clean, modern)
- F) Other (describe it, I'll translate to art direction)

"Setting?"
- Just a keyword: space / medieval / urban / forest / underwater / hell / school...
- If no idea, I'll recommend based on your game theme

### Step 4: Content Scope

Quick confirm (has defaults, user can skip entirely):

- Level count? Default: **3 levels** (easy intro → ramp up → final boss)
- If user has no strong opinion, use default and continue

**"Whatever" fast-track**: If user said "you decide" multiple times in Steps 2-4, skip remaining questions, assemble prompt with all recommended defaults, then let user review in Step 6.

### Step 5: Assemble Prompt

Combine collected info into OpenGame-ready prompt format:

```
Build a [type] game [theme/IP].
[Core gameplay — 2-3 sentences on what the player does].
[Character abilities — list specific attacks/skills].
[Enemy design — types and behaviors].
[Level structure — how many, scene descriptions].
[Visual style — one sentence anchoring art direction].
[UI/feedback — health bars, score, effects, etc.].
```

### Step 6: Review & Refine

Show assembled prompt to user:
- "Does this match your vision? Anything to adjust?"
- If user is happy, provide final prompt and suggest invoking `opengame` skill to generate

## Good Prompt vs Bad Prompt

**❌ Bad prompt:**
> Make a fun shooting game

**✅ Good prompt:**
> Build a side-scrolling action platformer starring a space marine fighting through 3 levels: an Alien Hive, a Crashed Spaceship, and a Volcanic Planet. The player has a blaster (ranged), a plasma sword (melee combo), and a screen-clearing Orbital Strike ultimate. Enemies include patrol drones, charging aliens, and a final boss with 3 phases (shield → rage → self-destruct). Art style: gritty 16-bit sci-fi pixel art with neon highlights. Show health bar, ammo count, and boss HP. Screen shake on explosions.

## Key Principles

1. **Specific beats vague** — "damage=30, HP=100" is better than "appropriate damage"
2. **Mechanics beat theme** — nail the gameplay rules first, then wrap with story
3. **Constraints beat freedom** — explicit limits (3 levels, 2 weapons) produce better output than "rich content"
4. **English prompts preferred** — OpenGame's template and GDD systems are English-based; English prompts yield higher quality
5. **Single HTML optional** — for simple games, add "Single HTML file, Canvas rendering" to simplify output

## Integration with opengame skill

After prompt is finalized:
1. Confirm final prompt with user
2. Suggest using `opengame` skill to generate the game
3. After generation, use `s3-deploy` skill to deploy to CDN

## Example Conversation

**User**: I want to make a cat tower defense game

**Coach guidance**:
1. Classify → tower_defense ✓
2. Mechanics → 3 cat towers (Sniper Siamese, AOE Fat Orange Cat, Slow Ragdoll Cat), enemies are mice/vacuums/cucumbers
3. Visuals → hand-drawn Kawaii, pastel palette
4. Scope → 5 waves, final wave boss is a Giant Roomba
5. Assemble prompt →

```
Build a hilarious tower defense game where cute cats defend a Golden Tuna Can from household pests. Towers: Sniper Siamese (long range, single target), Fat Orange Cat (throws buns for AOE splash), and Ragdoll Cat (slows enemies in area). Enemies: mice (fast, low HP), cucumbers (medium, cats get scared debuff), vacuum cleaners (tanky, boss-type). 5 waves with increasing difficulty, final wave boss is a Giant Roomba with shield phases. Art style: hand-drawn pastel Kawaii with bouncy animations. Show: wave counter, gold/tuna currency, cat mood indicators.
```
