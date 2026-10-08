# Archery SQL 审核平台 — 安全策略配置说明

## 系统信息

| 项目 | 值 |
| --- | --- |
| 系统名称 | Archery SQL 审核查询平台 |
| 版本 | v1.14 |
| 访问地址 | http://archery.itripo3d.com |
| 框架 | Django 4.x |
| 部署环境 | 阿里云 ECS |

## 一、密码复杂度策略

配置文件：`/opt/archery/archery/settings.py`

```json
{
  "AUTH_PASSWORD_VALIDATORS": [
    {
      "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
      "DESC": "密码不能与用户名、邮箱等个人信息过于相似"
    },
    {
      "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
      "OPTIONS": { "min_length": 9 },
      "DESC": "密码最小长度 9 位"
    },
    {
      "NAME": "django.contrib.auth.password_validation.MixedCasePasswordValidator",
      "DESC": "密码必须包含大小写字母"
    },
    {
      "NAME": "django.contrib.auth.password_validation.SpecialCharacterPasswordValidator",
      "DESC": "密码必须包含特殊字符"
    }
  ]
}
```

## 二、最长密码期限

```json
{
  "password_max_age_days": "未配置",
  "说明": "Archery 基于 Django 框架，Django 原生不提供密码过期强制改密机制，需引入第三方包（如 django-password-policies-iplweb）实现"
}
```

## 三、密码历史记忆

```json
{
  "password_history_count": "未配置",
  "说明": "Django 原生不记录密码修改历史，无法限制新密码不能与前 N 次相同，需引入第三方扩展实现"
}
```

## 四、会话超时策略（账户锁定时长）

配置文件：`/opt/archery/archery/settings.py`

```json
{
  "SESSION_COOKIE_AGE": 18000,
  "说明": "会话有效期 18000 秒（300 分钟），连续 300 分钟无操作自动过期，需重新输入密码登录",
  "SESSION_SAVE_EVERY_REQUEST": true,
  "说明2": "每次请求刷新超时倒计时，即用户持续操作期间不会过期",
  "SESSION_EXPIRE_AT_BROWSER_CLOSE": true,
  "说明3": "关闭浏览器后会话立即失效，需重新登录"
}
```

## 五、最大试错次数（账号锁定）

配置位置：Archery 系统配置表（`sql_config`），可通过后台「系统管理 → 系统配置」页面修改

代码位置：`/opt/archery/common/auth.py`

```json
{
  "lock_cnt_threshold": 5,
  "说明": "密码连续输入错误 5 次后锁定账号，锁定期间该账号无法登录",
  "lock_time_threshold": 300,
  "说明2": "账号锁定时长 300 秒（5 分钟），锁定期满后自动解锁，失败计数器重置"
}
```

锁定判断逻辑代码片段（`/opt/archery/common/auth.py`）：

```python
# 读取配置
lock_count = int(self.sys_config.get("lock_cnt_threshold", 5))
lock_time = int(self.sys_config.get("lock_time_threshold", 60 * 5))

# 验证是否在锁定期间
if user.failed_login_count >= lock_count:
    if user.last_login_failed_at + timedelta(seconds=lock_time) > now:
        return {"status": 3, "msg": "登录失败超过限制，该账号已被锁定！"}
    else:
        user.failed_login_count = 0  # 锁定期满，重置计数器

# 登录失败，累加计数
user.failed_login_count += 1
user.last_login_failed_at = datetime.now()
```

## 安全策略汇总

| 策略项 | 状态 | 当前值 | 配置位置 |
| --- | --- | --- | --- |
| 密码最小长度 | ✅ 已配置 | 9 位 | settings.py AUTH_PASSWORD_VALIDATORS |
| 密码复杂度 | ✅ 已配置 | 不能与用户名相似、必须包含大小写字母、必须包含特殊字符 | settings.py AUTH_PASSWORD_VALIDATORS |
| 会话超时锁定 | ✅ 已配置 | 300 分钟无操作过期，关闭浏览器立即失效 | settings.py SESSION_COOKIE_AGE |
| 最大试错次数 | ✅ 已配置 | 连续错误 5 次锁定账号 | 系统配置表 lock_cnt_threshold |
| 账号锁定时长 | ✅ 已配置 | 锁定 300 秒（5 分钟） | 系统配置表 lock_time_threshold |
| 最长密码期限 | ❌ 未配置 | 框架不支持，需第三方扩展 | — |
| 密码历史记忆 | ❌ 未配置 | 框架不支持，需第三方扩展 | — |
