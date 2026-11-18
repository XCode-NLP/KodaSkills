---
name: windows-builder
description: "Сборка образов Windows в Packer через коммуникатор WinRM и провижинеры PowerShell. Используй при создании Windows AMI, образов Azure или шаблонов VMware."
license: MPL-2.0
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
---

# Сборка образов Windows

Платформенно-независимые приёмы сборки образов Windows в Packer.

**Справка:** [WinRM Communicator](https://developer.hashicorp.com/packer/docs/communicators/winrm)

> **Замечание:** сборка Windows стоит заметных денег и времени. Ожидай 45–120 минут на сборку из-за обновлений Windows. Неудачные сборки могут оставить ресурсы запущенными — всегда проверяй, что всё убрано.

## Настройка коммуникатора WinRM

Для связи Packer с Windows нужен WinRM.

### Пример для AWS

```hcl
source "amazon-ebs" "windows" {
  region        = "us-west-2"
  instance_type = "t3.medium"

  source_ami_filter {
    filters = {
      name = "Windows_Server-2022-English-Full-Base-*"
    }
    most_recent = true
    owners      = ["amazon"]
  }

  ami_name = "windows-server-2022-${local.timestamp}"

  communicator   = "winrm"
  winrm_username = "Administrator"
  winrm_use_ssl  = true
  winrm_insecure = true
  winrm_timeout  = "15m"

  user_data_file = "scripts/setup-winrm.ps1"
}
```

### Скрипт настройки WinRM (scripts/setup-winrm.ps1)

```powershell
<powershell>
# Configure WinRM
winrm quickconfig -q
winrm set winrm/config '@{MaxTimeoutms="1800000"}'
winrm set winrm/config/service '@{AllowUnencrypted="true"}'
winrm set winrm/config/service/auth '@{Basic="true"}'

# Configure firewall
netsh advfirewall firewall add rule name="WinRM 5985" protocol=TCP dir=in localport=5985 action=allow
netsh advfirewall firewall add rule name="WinRM 5986" protocol=TCP dir=in localport=5986 action=allow

# Restart WinRM
net stop winrm
net start winrm
</powershell>
```

### Пример для Azure

```hcl
source "azure-arm" "windows" {
  client_id       = var.client_id
  client_secret   = var.client_secret
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id

  managed_image_resource_group_name = "images-rg"
  managed_image_name                = "windows-${local.timestamp}"

  os_type         = "Windows"
  image_publisher = "MicrosoftWindowsServer"
  image_offer     = "WindowsServer"
  image_sku       = "2022-datacenter-g2"

  location = "East US"
  vm_size  = "Standard_D2s_v3"

  # Azure сам настраивает WinRM
  communicator   = "winrm"
  winrm_use_ssl  = true
  winrm_insecure = true
  winrm_timeout  = "15m"
  winrm_username = "packer"
}
```

## Провижинеры PowerShell

### Установка программ

```hcl
build {
  sources = ["source.amazon-ebs.windows"]

  # установить Chocolatey
  provisioner "powershell" {
    inline = [
      "Set-ExecutionPolicy Bypass -Scope Process -Force",
      "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    ]
  }

  # установить приложения
  provisioner "powershell" {
    inline = [
      "choco install -y googlechrome",
      "choco install -y 7zip",
    ]
  }

  # установить IIS
  provisioner "powershell" {
    inline = [
      "Install-WindowsFeature -Name Web-Server -IncludeManagementTools"
    ]
  }
}
```

### Обновления Windows

```hcl
provisioner "powershell" {
  inline = [
    "Install-PackageProvider -Name NuGet -Force",
    "Install-Module -Name PSWindowsUpdate -Force",
    "Import-Module PSWindowsUpdate",
    "Get-WindowsUpdate -Install -AcceptAll -AutoReboot",
  ]
  timeout = "2h"
}

# дождаться перезагрузок
provisioner "windows-restart" {
  restart_timeout = "30m"
}
```

## Очистка

```hcl
provisioner "powershell" {
  inline = [
    "# Clear temp files",
    "Remove-Item -Path 'C:\\Windows\\Temp\\*' -Recurse -Force -ErrorAction SilentlyContinue",
    "# Clear Windows Update cache",
    "Stop-Service -Name wuauserv -Force",
    "Remove-Item -Path 'C:\\Windows\\SoftwareDistribution\\*' -Recurse -Force -ErrorAction SilentlyContinue",
    "Start-Service -Name wuauserv",
  ]
}
```

## Частые проблемы

**Таймаут WinRM**
- Увеличь `winrm_timeout` до 15 минут или больше.
- Проверь, что группа безопасности разрешает порты 5985 и 5986.
- Проверь, что скрипт в `user_data` выполнился успешно.

**Политика выполнения PowerShell**
```hcl
provisioner "powershell" {
  inline = [
    "Set-ExecutionPolicy Bypass -Scope Process -Force",
    "# Your commands here",
  ]
}
```

**Долгая сборка**
- Обновления Windows могут занимать 1–2 часа.
- Используй заранее пропатченные базовые образы, когда они есть.
- Задай у провижинера `timeout = "2h"`.

## Ссылки

- [WinRM Communicator](https://developer.hashicorp.com/packer/docs/communicators/winrm)
- [PowerShell Provisioner](https://developer.hashicorp.com/packer/docs/provisioners/powershell)
