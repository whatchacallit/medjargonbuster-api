#!/bin/bash

# Generates a RBAC Service Principal.
# GitHub Actions expects the output of this in your repo secret called "AZURE_CREDENTIALS"
az ad sp create-for-rbac --name "JargonBusterPrincipal" --sdk-auth