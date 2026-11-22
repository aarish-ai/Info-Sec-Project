# Task 1 Brief: Master CSS Tokens & Component Primitives

**Repository Path:** `d:\Projects\Unii\IS Project`
**Files to Modify:**
- `app/static/css/variables.css`
- `app/static/css/style.css`
- `tests/test_frontend.py`

**Requirements:**
1. Update `tests/test_frontend.py` with `test_tactical_obsidian_tokens_exist()` testing tokens:
   `--bg-void`, `--bg-chassis`, `--bg-plate`, `--bg-aperture`, `--lava-core`, `--signal-emerald`, `--signal-amber`, `--font-display`.
2. Update `app/static/css/variables.css`:
   - Import Google Fonts: `Space Grotesk`, `JetBrains Mono`, `Inter`.
   - Set Obsidian canvas: `--bg-void: #050507`, `--bg-chassis: #0b0c10`, `--bg-plate: #121319`, `--bg-aperture: #08090d`, `--bg-subplate: #181a24`.
   - Map existing tokens `--bg-base`, `--bg-surface`, `--bg-elevated`, `--bg-card` to these obsidian values.
   - Hairlines: `--border-laser: #1f222e`, `--border-tactical: #2b3042`, `--border-focus-laser: #ff2a4b`.
   - Lava Red Core: `--lava-core: #ff2a4b`, `--lava-hot: #ff4765`, `--lava-ember: #b3142d`, `--lava-glow: rgba(255, 42, 75, 0.20)`, `--lava-dim: rgba(255, 42, 75, 0.08)`.
   - Map `--primary` to `--lava-core`, `--primary-hover` to `--lava-hot`, `--primary-glow` to `--lava-glow`.
   - Signals: `--signal-emerald: #00e599`, `--signal-crimson: #ff2a4b`, `--signal-amber: #ffaa00`, `--signal-cyan: #00f0ff`.
   - Map `--success` to `--signal-emerald`, `--danger` to `--signal-crimson`, etc.
   - Fonts: `--font-display: 'Space Grotesk', -apple-system, sans-serif`, `--font-sans: 'Inter', -apple-system, sans-serif`, `--font-mono: 'JetBrains Mono', 'Fira Code', monospace`.
   - Strict 2px corners: `--radius-sm: 2px`, `--radius-md: 2px`, `--radius-lg: 3px`, `--radius-full: 2px`.
   - Preserve all existing token names from `test_css_variables_contain_all_design_tokens`.
3. Update `app/static/css/style.css`:
   - Redesign all components to match the tactical obsidian/lava aesthetic:
     - `.card-glass`: Milled basalt plate (`#121319`), hairline border (`#1f222e`), 2px radius, corner reticles (`::before`, `::after`).
     - `.btn`, `.btn-primary` (lava core `#ff2a4b`, sharp 2px, mechanical click travel `translateY(1px)` on `:active`, top bevel), `.btn-secondary`, `.btn-danger`, `.btn-outline`.
     - `.badge-status`, `.badge-authentic`, `.badge-modified`, `.badge-warning`, `.badge-info`, `.badge-role`: 2px rectangular chips with monospace bracket styling and glowing LED indicators.
     - `.input-terminal`: Recessed well (`#08090d`), hairline border, laser red focus border.
     - `.table-vault`: Tactical data table with hairline borders, tabular numerals, hover laser sweep line.
     - `.dropzone`: Recessed aperture with laser sweep animation on hover.
     - Preserve all classes required by `test_style_css_contains_all_component_classes`.
4. Run `python -m pytest tests/test_frontend.py -v` and ensure all tests pass.
5. Commit changes: `git add . && git commit -m "style: implement obsidian and lava red master design tokens and tactical component primitives"`.
