# Configure the Azure provider
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0.0"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

resource "azurerm_resource_group" "rg" {
  name     = "alevel-chess-rg"
  location = "westeurope"
}

# Random string for unique naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Web App Service Plan
resource "azurerm_service_plan" "webapp_asp" {
  name                = "plan${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location           = azurerm_resource_group.rg.location
  os_type            = "Linux"
  sku_name           = "F1" # Free tier

  timeouts {
    create = "30m"
  }

  depends_on = [
    azurerm_resource_group.rg
  ]
}

# Web App for Python Flask Application
resource "azurerm_linux_web_app" "webapp" {
  name                = "app${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.rg.name
  location           = azurerm_resource_group.rg.location
  service_plan_id    = azurerm_service_plan.webapp_asp.id

  site_config {
    application_stack {
      python_version = "3.9"
    }
    always_on = false
    minimum_tls_version = "1.2"
    ftps_state = "Disabled"
  }

  app_settings = {
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "DEPLOYMENT_BRANCH"            = "main"
    "WEBSITES_CONTAINER_SSH_ENABLED" = "false"
  }

  timeouts {
    create = "30m"
  }

  depends_on = [
    azurerm_service_plan.webapp_asp,
  ]
}
