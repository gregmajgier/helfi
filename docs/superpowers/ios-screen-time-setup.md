# iOS Screen Time: Entitlement Request and Setup

Status: not started, needs you (Account Holder) to submit the Apple request.
Written: 2026-10-05. Part of [native screen-time tracking](specs/2026-10-05-screen-time-tracking-design.md), milestone 4.

Nothing iOS-specific is integrated yet. `src/modules/screen_time/usage.ios.ts` is a typed stub that reports
"unavailable", so iPhone builds work exactly as before. Android ships first.

## What is verified and what is not

| Claim | Source |
| --- | --- |
| Needs Apple team ID and an App Group; creates extension targets `ActivityMonitorExtension`, `ShieldAction`, `ShieldConfiguration`; min iOS 15.1; no Expo Go; one Apple request per bundle ID; 20-monitor limit | `react-native-device-activity` README (fetched 2026-10-05) |
| The request form lives at `developer.apple.com/contact/request/family-controls-distribution` | Opens a sign-in redirect, so the URL exists. I could not read the form behind the login. |
| Form fields, who may submit, review time | **Not verified.** Treat the notes below as expectations and follow what the form actually asks. |

## 1. Decide the bundle identifier (permanent)

`app.json` has no `ios.bundleIdentifier` yet. The Apple request is per bundle ID and an App Store bundle ID cannot
be changed later, so pick it now. My proposal, which you should change if you prefer another reverse-DNS name:

| Target | Bundle ID |
| --- | --- |
| Main app | `com.gregmajgier.helf` |
| Activity monitor extension | `com.gregmajgier.helf.ActivityMonitor` |
| Shield action extension | `com.gregmajgier.helf.ShieldAction` |
| Shield configuration extension | `com.gregmajgier.helf.ShieldConfiguration` |

helf only needs the monitor extension, but the library generates all three extensions and its README says each of
the four identifiers needs its own approval, so request all four.

Use the same base for Android (`android.package`) so the two stores line up.

## 2. Apple Developer portal prep

1. Enrol in the paid Apple Developer Program (individual or organisation). The Distribution request and App Store
   builds need it. I did not verify whether the free tier can use the Development entitlement for local builds.
2. Certificates, Identifiers & Profiles, Identifiers: register the four explicit App IDs above.
3. Identifiers, App Groups: register `group.com.gregmajgier.helf`. Add it to all four App IDs (the monitor
   extension writes usage there, the app reads it).
4. Note your 10-character **Team ID** (Membership details). It goes into the config plugin.

## 3. Request the Family Controls (Distribution) entitlement

1. Sign in as the Account Holder and open `https://developer.apple.com/contact/request/family-controls-distribution`.
2. Submit the form once per bundle ID (four submissions), using the identifiers from section 1.
3. Use this justification, adjusted to what the form asks:

   > helf is a personal wellbeing app. With Family Controls in individual authorization, a user can see how much
   > time they spend in non-productive apps and set a daily budget shown as a progress ring. The app never
   > blocks apps for another person, never reads app names or content, and uploads only a daily total of minutes
   > to the user's own account. The user chooses which apps count as productive with the system activity picker.
   > We use DeviceActivity threshold events (15-minute steps) to estimate daily time.

4. Do not wait idle: Android and the rest of the app proceed in parallel.
5. While approval is pending you can only build locally in Xcode with the **Development** entitlement on devices
   registered to your team. EAS dev client and TestFlight builds need the approved Distribution entitlement.

## 4. Config plugin settings (apply after approval, or for local Xcode builds)

Install (not done yet, because the plugin needs a real Team ID and would break `expo prebuild` without it):

```sh
npx expo install expo-build-properties
npm install react-native-device-activity
```

`app.json`, under `expo`:

```json
{
  "ios": {
    "bundleIdentifier": "com.gregmajgier.helf"
  },
  "plugins": [
    ["expo-build-properties", { "ios": { "deploymentTarget": "15.1" } }],
    [
      "react-native-device-activity",
      {
        "appleTeamId": "<YOUR_TEAM_ID>",
        "appGroup": "group.com.gregmajgier.helf"
      }
    ]
  ]
}
```

Check the Expo SDK 57 minimum iOS deployment target first. If it is above 15.1, keep the higher value and drop the
`expo-build-properties` line. The two plugin options (`appleTeamId`, `appGroup`) are the only required ones in the
README. Do not commit the Team ID if you treat it as private (it is not secret, but is account-identifying); an
`app.config.ts` reading it from an env var works too.

After `npx expo prebuild --platform ios` confirm Xcode shows targets `ActivityMonitorExtension`, `ShieldAction` and
`ShieldConfiguration`, each with the Family Controls capability and the App Group. Then run on a **physical
iPhone**; the Screen Time APIs do not work in the simulator or Expo Go.

## 5. Integration plan once approved (replaces the stub)

Follows the spec's iOS section.

1. `usage.ios.ts`: authorization with the library's individual `requestAuthorization`, `getPermissionState` mapping
   to `granted | denied`. Check the library's current API names in its README before coding; they are not pinned here.
2. Excluded apps: present the system `FamilyActivityPicker` (the only way to choose apps) for the productive set.
   Store the returned selection id, not the raw tokens (tokens can be very large). `pickerMode` becomes `"system"`;
   `ScreenTimeSection` needs a branch for it, because it currently renders the Android list only.
3. Monitoring: schedule a daily `DeviceActivity` monitor over "all apps and categories minus the excluded
   selection", with threshold events every `IOS_THRESHOLD_STEP_MINUTES` (15) up to the budget plus headroom.
   Mind the 20-monitor limit.
4. The monitor extension writes the highest threshold reached, as `IosSharedUsage`, to the App Group. The app reads it
   in `getDailyUsage`, returning `dumb_minutes = highest_threshold_minutes` and `total_minutes = dumb_minutes`
   (iOS cannot report the excluded time, so total is not meaningful there; the backend only needs
   `dumb_minutes <= total_minutes`).
5. Keep the accuracy note: "approximate on iPhone".
6. Test on a physical iPhone: authorization, picker, a threshold firing, midnight rollover, app killed in background.

## Checklist

- [ ] Choose and confirm the bundle ID base
- [ ] Register 4 App IDs and the App Group
- [ ] Submit 4 Family Controls (Distribution) requests
- [ ] Add the Team ID and plugin config, prebuild, check the 3 extension targets
- [ ] Implement `usage.ios.ts` per section 5 and test on a physical iPhone
