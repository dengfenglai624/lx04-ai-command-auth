package com.lx04.codexauth;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/**
 * 开机自启动接收器
 */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction()) || Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent.getAction())) {
            // 检查悬浮窗权限
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.M) {
                if (android.provider.Settings.canDrawOverlays(context)) {
                    if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                        context.startForegroundService(new Intent(context, OverlayService.class));
                    } else {
                        context.startService(new Intent(context, OverlayService.class));
                    }
                }
            } else {
                context.startService(new Intent(context, OverlayService.class));
            }
        }
    }
}
