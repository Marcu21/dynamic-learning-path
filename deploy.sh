#!/bin/bash
set -e

# Use environment variables or defaults
REMOTE_HOST=${REMOTE_HOST:-"ssh-interns.ccrolabs.com"}
REMOTE_USER=${REMOTE_USER:-"bocrarazvan"}
REMOTE_PATH=${REMOTE_PATH:-"/Users/Shared/case-ai-dynamic-learning-path"}
SSH_PORT=22
DOCKER_CMD="/usr/local/bin/docker"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Helper to run a command as ROOT on the remote server
ssh_root_cmd() {
    local cmd_to_run_as_root="$1"
    CF_CLIENT_ID=${CF_CLIENT_ID} CF_CLIENT_SECRET=${CF_CLIENT_SECRET} \
    echo "$SSH_PASSWORD" | ssh -p $SSH_PORT -o ProxyCommand="cloudflared access ssh --hostname %h" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "sudo -S ${cmd_to_run_as_root}"
}

# Helper to run a command as the 'computacenterro' USER on the remote server
ssh_user_cmd() {
    local cmd_to_run_as_user="$1"
    # The '-i' flag simulates a full, clean login for the user, fixing all permission warnings.
    local full_cmd="sudo -S -i -u computacenterro bash -c '$cmd_to_run_as_user'"
    CF_CLIENT_ID=${CF_CLIENT_ID} CF_CLIENT_SECRET=${CF_CLIENT_SECRET} \
    echo "$SSH_PASSWORD" | ssh -p $SSH_PORT -o ProxyCommand="cloudflared access ssh --hostname %h" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$full_cmd"
}

# SCP file transfer helper
scp_file() {
    local local_file="$1"
    local remote_file="$2"
    CF_CLIENT_ID=${CF_CLIENT_ID} CF_CLIENT_SECRET=${CF_CLIENT_SECRET} \
    sshpass -p "$SSH_PASSWORD" scp -P $SSH_PORT -o ProxyCommand="cloudflared access ssh --hostname %h" -o StrictHostKeyChecking=no "$local_file" "$REMOTE_USER@$REMOTE_HOST:$remote_file"
}

# --- Main Script ---

log "Checking required files..."
[[ -f "be/.env.prod" ]] || error "be/.env.prod not found"
[[ -f "fe/.env.prod" ]] || error "fe/.env.prod not found"
[[ -f "be/gcp-credentials.json" ]] || error "be/gcp-credentials.json not found"

log "Transferring files..."
scp_file "be/.env.prod" "$REMOTE_PATH/be/.env"
scp_file "fe/.env.prod" "$REMOTE_PATH/fe/.env"
scp_file "be/gcp-credentials.json" "$REMOTE_PATH/be/gcp-credentials.json"

log "Setting file ownership..."
ssh_root_cmd "chown computacenterro:staff $REMOTE_PATH/be/.env $REMOTE_PATH/fe/.env $REMOTE_PATH/be/gcp-credentials.json"

log "Pulling latest code..."
ssh_user_cmd "cd $REMOTE_PATH && git reset --hard origin/main && git pull"

log "Stopping all containers..."
# Removed the '--remove-orphans' flag, as it's default behavior now.
ssh_user_cmd "cd $REMOTE_PATH && $DOCKER_CMD compose down"

log "Starting containers from backend..."
ssh_user_cmd "cd $REMOTE_PATH/be && $DOCKER_CMD compose up --build"
log "✅ Deployment complete!"
log "Services should be available shortly."