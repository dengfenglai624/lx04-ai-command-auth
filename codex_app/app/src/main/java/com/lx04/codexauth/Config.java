package com.lx04.codexauth;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * 运行时配置：电脑端服务地址。
 * 优先级：用户设置(SharedPreferences) > 编译期默认值(BuildConfig)。
 */
public final class Config {

    private static final String PREFS = "lx04_config";
    private static final String KEY_AUTH_URL = "auth_server_url";
    private static final String KEY_QUOTA_URL = "quota_server_url";

    private Config() {
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    /** 授权服务地址，如 http://192.168.1.10:8080 */
    public static String getAuthUrl(Context context) {
        return trim(prefs(context).getString(KEY_AUTH_URL, BuildConfig.AUTH_SERVER_URL));
    }

    /** 额度服务地址，如 http://192.168.1.10:8081 */
    public static String getQuotaUrl(Context context) {
        return trim(prefs(context).getString(KEY_QUOTA_URL, BuildConfig.QUOTA_SERVER_URL));
    }

    public static void setAuthUrl(Context context, String url) {
        prefs(context).edit().putString(KEY_AUTH_URL, trim(url)).apply();
    }

    public static void setQuotaUrl(Context context, String url) {
        prefs(context).edit().putString(KEY_QUOTA_URL, trim(url)).apply();
    }

    private static String trim(String url) {
        if (url == null) return "";
        String value = url.trim();
        while (value.endsWith("/")) {
            value = value.substring(0, value.length() - 1);
        }
        return value;
    }
}
