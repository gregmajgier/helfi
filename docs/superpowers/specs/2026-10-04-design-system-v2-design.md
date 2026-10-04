# Design System v2 (Bold & Playful) - Design Spec

Status: Draft, direction approved in chat 2026-10-04 (autonomous follow-through)
Owner: gregmajgier@gmail.com
Depends on: [helf Rebrand, Design System & Onboarding](2026-10-02-helf-brand-onboarding-design.md)
Consumed by: [Today Dashboard Layout](2026-10-04-dashboard-layout-design.md)
(supersedes that spec's "Visual direction" section)

## Purpose

The review doc asks for a more vibrant app. The current system is tasteful
but flat: warm neutral background, thin bordered surfaces, emoji as icons,
no depth, no motion. v2 keeps the architecture (`src/lib/theme.ts` tokens +
`src/components/` primitives, Plus Jakarta Sans, four pillars) and replaces
the look: a new bolder palette, colored surfaces, depth, real icons, and
purposeful motion.

Decisions made in chat: direction "Bold & playful", real icon library for
pillar icons (mood faces stay emoji, they are expressive content), "rich"
motion, palette replaced from scratch, shared components rebuilt (not just
re-skinned). No third-party UI kit.

Out of scope: screen-level layout changes (dashboard and onboarding have
their own specs), backend, data logic.

## Tokens (`src/lib/theme.ts`)

Platform note: this is React Native, so web-oriented guidance (Tailwind,
CSS blur, GSAP) is replaced by RN equivalents below.

- **Neutrals** (cooler than v1 so the saturated pillars pop):
  - Light: background `#F6F6FB`, surface `#FFFFFF`, textPrimary `#14151F`,
    textSecondary `#5A5E72`, border `#E2E3EE`.
  - Dark: background `#0E0F16`, surface `#181A24`, textPrimary `#F5F5FA`,
    textSecondary `#9A9EB2`, border `#262936`.
- **Pillars** (four clearly distinct hues, each with `light`, `dark`, and a
  derived `tint`):
  - Move `#FF5A36` / dark `#FF7A5C`
  - Fuel `#22B866` / dark `#46D58A`
  - Mind `#7A5CFF` / dark `#9C85FF`
  - Focus `#1E9BFF` / dark `#52B4FF`
  - `tint(color, alpha)` helper returns the color at alpha (default 0.14 for
    surfaces, 0.28 for icon badges). Text on a solid pillar fill is always
    `#FFFFFF` except Fuel and Focus light, which use `#0B1A12`/`#06192B`
    where white contrast is under 4.5:1 (verified in tests).
- **Radius scale (shape lock)**: `sm 12` inputs/small controls, `md 18`
  buttons and stat tiles, `lg 24` cards and pillar tiles, `pill 999` chips
  and badges only. No other radii in components.
- **Shadows**: `shadow.card` (neutral, soft) and `shadow.accent(color)`
  (tinted to a pillar color, used on filled buttons and pillar cards).
  iOS uses `shadowColor/Opacity/Radius/Offset`; Android only supports
  neutral `elevation`, so tinted shadows degrade to elevation there
  (documented limitation, acceptable).
- **Spacing and font**: unchanged. Add `motion` constants: `spring = {
  damping: 16, stiffness: 220 }`, `pressScale = 0.96`, `stagger = 60ms`,
  `enterDuration = 420ms`.

## Icons

Add `phosphor-react-native` (one icon family app-wide, `duotone` weight,
primary color = pillar color, secondary tint from `tint()`). New
`src/components/PillarIcon.tsx` maps pillar to icon: Move `Barbell`, Fuel
`ForkKnife`, Mind `Brain`, Focus `Timer`. It requires `react-native-svg`
(also needed by the dashboard rings). `PILLARS[...].icon` emoji field is
removed. Mood faces in mental-health stay emoji.

## Components (rebuilt)

- `AnimatedPressable` (new base): Reanimated spring scale to `pressScale`
  on press, back on release; reduced motion falls back to opacity only.
  `Button`, `Chip`, `PillarTile`, and pressable cards build on it.
- `Button`: variants `primary` (solid accent fill, tinted shadow, white or
  dark label per contrast rule), `secondary` (tinted fill 14%, accent
  label), `text`. Radius `md`, min height 52.
- `Card`: surface fill, `lg` radius, `shadow.card`, optional `accent` prop
  that switches to a pillar-tinted fill instead of a border. Border only in
  dark mode.
- `Chip`: pill, selected = solid accent fill, unselected = tinted fill (not
  outlined), spring on press.
- `PillarTile`: pillar-tinted fill, `PillarIcon` in a tinted circular
  badge, bold label, status line, tinted accent shadow, enters with stagger.
- `ProgressDots`: active dot width animates with a spring.
- `ScreenContainer`: unchanged contract, new background token.
- New `Screen entrance`: items use Reanimated `FadeInUp.springify()` with
  `stagger` delay via a small `useEnter(index)` helper in `src/lib/motion.ts`.
- `src/lib/motion.ts`: `useReducedMotion()` (reads
  `AccessibilityInfo.isReduceMotionEnabled` and subscribes to
  `reduceMotionChanged`), `useEnter(index)`, shared spring constants. When
  reduced motion is on, entering animations are omitted and press feedback
  is opacity-only.

## Rollout

All screens already import the shared components and `useTheme`, so the
refresh propagates automatically. A grep pass replaces: raw `Pressable`
buttons that should be `AnimatedPressable`, hardcoded colors (`#FFFFFF`,
`#C0392B`) with tokens (add `colors.danger`), and any use of
`PILLARS[..].icon`. Wordmark "helf" gets a four-pillar-color treatment.

## Dependencies

`phosphor-react-native`, `react-native-svg`. `react-native-reanimated` is
already installed. Per `AGENTS.md`, verify install commands and Reanimated
config (babel/worklets plugin) against
https://docs.expo.dev/versions/v57.0.0/ before adding.

## Testing

- Unit: `tint()` alpha math; contrast check test asserting every
  pillar/label color pair meets 4.5:1 in light and dark.
- Existing Jest suite stays green; `tsc` clean.
- Manual simulator pass in light and dark: shadows, tinted surfaces, icons,
  press feedback, entrance stagger, and Reduce Motion on disables springs.

## Error/edge handling

Icon import failure is not possible at runtime (static import). Android
tinted-shadow limitation noted above. Reduced motion handled globally in
`motion.ts`.
