#!/usr/bin/env bash
set -euo pipefail
DRIVE_NAME="Kingdom"
PLATFORM_ADMINS="platform-admins@kingdom.example"
PLATFORM_DEVS="platform-devs@kingdom.example"
SECURITY="security@kingdom.example"
READONLY="readonly@kingdom.example"

# Create groups with GAM
gam create group platform-admins description "Platform admins"
gam create group platform-devs description "Platform developers"
gam create group security description "Security team"
gam create group readonly description "Read-only auditors"

# Create shared drive
DRIVE_ID=$(gam create drive "$DRIVE_NAME" | awk '/Drive ID/ {print $NF}')
echo "Created Shared Drive $DRIVE_NAME ($DRIVE_ID)"

# Add group roles
gam update drivefileacl "$DRIVE_ID" group "$PLATFORM_ADMINS" role manager
gam update drivefileacl "$DRIVE_ID" group "$PLATFORM_DEVS" role writer
gam update drivefileacl "$DRIVE_ID" group "$SECURITY" role manager
gam update drivefileacl "$DRIVE_ID" group "$READONLY" role reader
echo "Assigned group permissions"
