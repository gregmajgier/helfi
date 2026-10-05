package expo.modules.screentime

import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.content.pm.ResolveInfo
import android.net.Uri
import android.os.Build
import android.os.Process
import android.provider.Settings
import expo.modules.kotlin.exception.Exceptions
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition
import expo.modules.kotlin.records.Field
import expo.modules.kotlin.records.Record

// Upper bounds so a bad caller (or a very busy device) cannot make us build an unbounded result.
private const val MAX_EVENTS = 50_000
private const val MAX_APPS = 2_000
private const val MAX_RANGE_MS = 48L * 60 * 60 * 1000

// UsageEvents.Event codes we forward. Raw numbers because several constants need a newer API
// level than minSdk; the values are stable. The interval logic lives in TypeScript
// (src/modules/screen_time/foreground.ts) and uses the same codes.
private val FORWARDED_EVENT_TYPES = setOf(
  1, // MOVE_TO_FOREGROUND / ACTIVITY_RESUMED
  2, // MOVE_TO_BACKGROUND / ACTIVITY_PAUSED
  16, // SCREEN_NON_INTERACTIVE
  23, // ACTIVITY_STOPPED
  26, // DEVICE_SHUTDOWN
)

class UsageEventRecord : Record {
  @Field
  var p: String = ""

  @Field
  var t: Int = 0

  @Field
  var ts: Double = 0.0
}

class LaunchableApp : Record {
  @Field
  var id: String = ""

  @Field
  var label: String = ""

  @Field
  var category: String? = null
}

class ScreenTimeModule : Module() {
  private val context: Context
    get() = appContext.reactContext ?: throw Exceptions.ReactContextLost()

  override fun definition() = ModuleDefinition {
    Name("ScreenTime")

    Function("hasUsageAccess") {
      hasUsageAccess()
    }

    Function("openUsageAccessSettings") {
      openUsageAccessSettings()
    }

    AsyncFunction("queryForegroundEvents") { startMs: Double, endMs: Double ->
      queryForegroundEvents(startMs.toLong(), endMs.toLong())
    }

    AsyncFunction("listLaunchableApps") {
      listLaunchableApps()
    }

    Function("getIgnoredPackages") {
      ignoredPackages().toList()
    }
  }

  private fun hasUsageAccess(): Boolean {
    val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
    val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
      appOps.unsafeCheckOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName)
    } else {
      @Suppress("DEPRECATION")
      appOps.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName)
    }
    if (mode == AppOpsManager.MODE_DEFAULT) {
      // Some OEM builds report DEFAULT while the manifest permission decides.
      return context.checkCallingOrSelfPermission(android.Manifest.permission.PACKAGE_USAGE_STATS) ==
        PackageManager.PERMISSION_GRANTED
    }
    return mode == AppOpsManager.MODE_ALLOWED
  }

  private fun openUsageAccessSettings() {
    val launcher = appContext.currentActivity ?: context
    val withPackage = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS).apply {
      data = Uri.parse("package:${context.packageName}")
      addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    }
    try {
      launcher.startActivity(withPackage)
    } catch (e: ActivityNotFoundException) {
      // Some devices cannot deep-link to our own entry; open the general list instead.
      launcher.startActivity(Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }
  }

  private fun queryForegroundEvents(startMs: Long, endMs: Long): List<UsageEventRecord> {
    require(startMs < endMs) { "start must be before end" }
    require(endMs - startMs <= MAX_RANGE_MS) { "range too large" }
    if (!hasUsageAccess()) return emptyList()

    val manager = context.getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
    val events = manager.queryEvents(startMs, endMs)
    val event = UsageEvents.Event()
    val result = ArrayList<UsageEventRecord>()
    while (events.hasNextEvent() && result.size < MAX_EVENTS) {
      events.getNextEvent(event)
      if (event.eventType !in FORWARDED_EVENT_TYPES) continue
      result.add(
        UsageEventRecord().apply {
          p = event.packageName ?: ""
          t = event.eventType
          ts = event.timeStamp.toDouble()
        }
      )
    }
    return result
  }

  private fun queryActivities(category: String): List<ResolveInfo> {
    val intent = Intent(Intent.ACTION_MAIN).addCategory(category)
    val pm = context.packageManager
    return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
      pm.queryIntentActivities(intent, PackageManager.ResolveInfoFlags.of(0))
    } else {
      @Suppress("DEPRECATION")
      pm.queryIntentActivities(intent, 0)
    }
  }

  private fun listLaunchableApps(): List<LaunchableApp> {
    val pm = context.packageManager
    val seen = HashSet<String>()
    val apps = ArrayList<LaunchableApp>()
    for (info in queryActivities(Intent.CATEGORY_LAUNCHER)) {
      val pkg = info.activityInfo.packageName
      if (pkg == context.packageName || !seen.add(pkg)) continue
      apps.add(
        LaunchableApp().apply {
          id = pkg
          label = info.loadLabel(pm).toString()
          category = categoryName(info.activityInfo.applicationInfo)
        }
      )
      if (apps.size >= MAX_APPS) break
    }
    return apps
  }

  private fun categoryName(info: ApplicationInfo): String? {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return null
    return when (info.category) {
      ApplicationInfo.CATEGORY_GAME -> "game"
      ApplicationInfo.CATEGORY_AUDIO -> "audio"
      ApplicationInfo.CATEGORY_VIDEO -> "video"
      ApplicationInfo.CATEGORY_IMAGE -> "image"
      ApplicationInfo.CATEGORY_SOCIAL -> "social"
      ApplicationInfo.CATEGORY_NEWS -> "news"
      ApplicationInfo.CATEGORY_MAPS -> "maps"
      ApplicationInfo.CATEGORY_PRODUCTIVITY -> "productivity"
      else -> null
    }
  }

  /** Packages that must never count: helf itself, System UI and every home screen app. */
  private fun ignoredPackages(): Set<String> {
    val ignored = HashSet<String>()
    ignored.add(context.packageName)
    ignored.add("com.android.systemui")
    for (info in queryActivities(Intent.CATEGORY_HOME)) {
      ignored.add(info.activityInfo.packageName)
    }
    return ignored
  }
}
