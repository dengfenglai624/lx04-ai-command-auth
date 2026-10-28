package com.lx04.codexauth;

import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

/**
 * 主界面 - 选择 AI 模式并启动授权服务
 */
public class MainActivity extends AppCompatActivity {

    private static final int OVERLAY_PERMISSION_CODE = 1001;
    private String selectedMode = "codex";
    private TextView serverText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        TextView statusText = findViewById(R.id.status_text);
        serverText = findViewById(R.id.server_text);
        Button btnPermission = findViewById(R.id.btn_permission);
        Button btnCodex = findViewById(R.id.btn_codex);
        Button btnWorkBuddy = findViewById(R.id.btn_workbuddy);
        Button btnStop = findViewById(R.id.btn_stop);

        refreshServerText();
        serverText.setOnClickListener(v -> showServerDialog());


        // 检查悬浮窗权限
        if (hasOverlayPermission()) {
            statusText.setText("✅ 悬浮窗权限已授予");
            btnPermission.setVisibility(View.GONE);
        } else {
            statusText.setText("⚠️ 需要悬浮窗权限");
            btnPermission.setOnClickListener(v -> requestOverlayPermission());
        }

        updateListeningStatus(getIntent());

        // Codex 模式
        btnCodex.setOnClickListener(v -> {
            if (!hasOverlayPermission()) {
                Toast.makeText(this, "请先授予悬浮窗权限", Toast.LENGTH_SHORT).show();
                return;
            }
            selectedMode = "codex";
            startServiceWithMode();
            statusText.setText("🟢 Codex 模式运行中");
            Toast.makeText(this, "Codex 模式已启动", Toast.LENGTH_SHORT).show();
        });

        // Work Buddy 模式
        btnWorkBuddy.setOnClickListener(v -> {
            if (!hasOverlayPermission()) {
                Toast.makeText(this, "请先授予悬浮窗权限", Toast.LENGTH_SHORT).show();
                return;
            }
            selectedMode = "workbuddy";
            startServiceWithMode();
            statusText.setText("🟢 Work Buddy 模式运行中");
            Toast.makeText(this, "Work Buddy 模式已启动", Toast.LENGTH_SHORT).show();
        });

        // 停止服务
        btnStop.setOnClickListener(v -> {
            stopService(new Intent(this, OverlayService.class));
            statusText.setText("⚪ 服务已停止");
            Toast.makeText(this, "服务已停止", Toast.LENGTH_SHORT).show();
        });
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        updateListeningStatus(intent);
    }

    private void updateListeningStatus(Intent intent) {
        if (intent != null && intent.getBooleanExtra("AUTH_SERVICE_RUNNING", false)) {
            selectedMode = intent.getStringExtra("MODE");
            if (selectedMode == null) selectedMode = "codex";
            TextView status = findViewById(R.id.status_text);
            status.setText("workbuddy".equals(selectedMode)
                ? "🟢 Work Buddy 模式运行中" : "🟢 Codex 模式运行中");
        }
    }

    private void startServiceWithMode() {
        Intent intent = new Intent(this, OverlayService.class);
        intent.putExtra("MODE", selectedMode);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent);
        } else {
            startService(intent);
        }
    }

    private boolean hasOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            return Settings.canDrawOverlays(this);
        }
        return true;
    }

    private void requestOverlayPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Intent intent = new Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:" + getPackageName())
            );
            startActivityForResult(intent, OVERLAY_PERMISSION_CODE);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == OVERLAY_PERMISSION_CODE) {
            if (hasOverlayPermission()) {
                TextView statusText = findViewById(R.id.status_text);
                statusText.setText("✅ 悬浮窗权限已授予");
                findViewById(R.id.btn_permission).setVisibility(View.GONE);
                Toast.makeText(this, "权限已授予！", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshServerText();
        // 刷新权限状态
        if (hasOverlayPermission()) {
            TextView statusText = findViewById(R.id.status_text);
            if (statusText.getText().toString().contains("需要")) {
                statusText.setText("✅ 悬浮窗权限已授予");
                findViewById(R.id.btn_permission).setVisibility(View.GONE);
            }
        }
    }

    private void refreshServerText() {
        if (serverText != null) {
            serverText.setText("SERVER: " + Config.getAuthUrl(this) + "  ✎");
        }
    }

    /** 修改电脑端服务地址：授权服务 / 额度服务 */
    private void showServerDialog() {
        LinearLayout container = new LinearLayout(this);
        container.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (16 * getResources().getDisplayMetrics().density);
        container.setPadding(pad, pad, pad, pad);

        TextView authLabel = new TextView(this);
        authLabel.setText("授权服务地址 (默认端口 8080)");
        container.addView(authLabel);

        EditText authInput = new EditText(this);
        authInput.setInputType(InputType.TYPE_TEXT_VARIATION_URI);
        authInput.setText(Config.getAuthUrl(this));
        container.addView(authInput);

        TextView quotaLabel = new TextView(this);
        quotaLabel.setText("额度服务地址 (默认端口 8081)");
        container.addView(quotaLabel);

        EditText quotaInput = new EditText(this);
        quotaInput.setInputType(InputType.TYPE_TEXT_VARIATION_URI);
        quotaInput.setText(Config.getQuotaUrl(this));
        container.addView(quotaInput);

        new AlertDialog.Builder(this)
            .setTitle("电脑端服务地址")
            .setView(container)
            .setPositiveButton("保存并重启服务", (dialog, which) -> {
                String auth = authInput.getText().toString().trim();
                String quota = quotaInput.getText().toString().trim();
                if (auth.isEmpty()) {
                    Toast.makeText(this, "授权服务地址不能为空", Toast.LENGTH_SHORT).show();
                    return;
                }
                if (!auth.startsWith("http://") && !auth.startsWith("https://")) {
                    auth = "http://" + auth;
                }
                if (!quota.isEmpty() && !quota.startsWith("http://") && !quota.startsWith("https://")) {
                    quota = "http://" + quota;
                }
                Config.setAuthUrl(this, auth);
                Config.setQuotaUrl(this, quota.isEmpty() ? auth.replaceAll(":\\d+$", ":8081") : quota);

                // 地址变更需要重启服务才会生效
                stopService(new Intent(this, OverlayService.class));
                if (hasOverlayPermission()) {
                    startServiceWithMode();
                }
                refreshServerText();
                Toast.makeText(this, "已保存：" + Config.getAuthUrl(this), Toast.LENGTH_LONG).show();
            })
            .setNegativeButton("取消", null)
            .show();
    }
}
