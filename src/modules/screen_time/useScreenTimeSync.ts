import { useEffect } from "react";
import { AppState } from "react-native";

import { syncScreenTime } from "./sync";

/** Syncs when the screen mounts and whenever the app returns to the foreground. Throttled inside `syncScreenTime`. */
export function useScreenTimeSync(enabled: boolean) {
  useEffect(() => {
    if (!enabled) return;
    void syncScreenTime();
    const subscription = AppState.addEventListener("change", (state) => {
      if (state === "active") void syncScreenTime();
    });
    return () => subscription.remove();
  }, [enabled]);
}
