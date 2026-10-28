# 默认混淆规则（debug 构建不启用混淆）
# 保持 Binder 调用与服务类不被裁剪
-keep class com.lx04.codexauth.** { *; }
