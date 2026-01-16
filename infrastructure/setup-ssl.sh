#!/bin/bash
# =============================================================================
# SSL Certificate Setup Script for Intelli
# Supports both Let's Encrypt and custom certificates (wildcard or standard)
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

DOMAIN="intell.cedia.org.ec"
SSL_DIR="nginx/ssl"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Certificate Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Create SSL directory
mkdir -p "$SSL_DIR"

# Check if certificates already exist
if [ -f "$SSL_DIR/fullchain.pem" ] && [ -f "$SSL_DIR/privkey.pem" ]; then
    echo -e "${YELLOW}SSL certificates already exist${NC}"
    read -p "Do you want to replace them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing certificates"
        exit 0
    fi
    # Backup existing certificates
    BACKUP_DIR="$SSL_DIR/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp "$SSL_DIR"/*.pem "$BACKUP_DIR/" 2>/dev/null || true
    echo "Existing certificates backed up to $BACKUP_DIR"
fi

echo "Choose SSL certificate setup method:"
echo "  1) Let's Encrypt (certbot) - Automatic"
echo "  2) Custom certificate files (wildcard or standard)"
echo "  3) Skip SSL setup"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}Setting up Let's Encrypt certificates...${NC}"
        
        # Check if certbot is installed
        if ! command -v certbot &> /dev/null; then
            echo "Installing certbot..."
            sudo apt-get update
            sudo apt-get install -y certbot
        fi
        
        # Check if nginx is running (needed for verification)
        if ! docker-compose -f docker-compose.prod.yml ps nginx | grep -q "Up"; then
            echo -e "${YELLOW}Starting nginx container for certificate verification...${NC}"
            docker-compose -f docker-compose.prod.yml up -d nginx || true
        fi
        
        # Request certificate
        echo "Requesting certificate for $DOMAIN..."
        sudo certbot certonly --webroot \
            -w "$SCRIPT_DIR/nginx/ssl/.well-known/acme-challenge" \
            -d "$DOMAIN" \
            --email admin@cedia.edu.ec \
            --agree-tos \
            --non-interactive || {
            echo -e "${RED}Failed to obtain certificate${NC}"
            echo "You may need to:"
            echo "  1. Ensure DNS points to this server"
            echo "  2. Ensure port 80 is accessible"
            echo "  3. Run this script again"
            exit 1
        }
        
        # Copy certificates to nginx/ssl
        CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
        if [ -d "$CERT_PATH" ]; then
            sudo cp "$CERT_PATH/fullchain.pem" "$SSL_DIR/"
            sudo cp "$CERT_PATH/privkey.pem" "$SSL_DIR/"
            sudo chown $USER:$USER "$SSL_DIR"/*.pem
            echo -e "${GREEN}Certificates copied to $SSL_DIR${NC}"
        else
            echo -e "${RED}Certificate files not found at $CERT_PATH${NC}"
            exit 1
        fi
        
        # Setup auto-renewal
        echo "Setting up auto-renewal..."
        (crontab -l 2>/dev/null | grep -v "certbot renew" || true; echo "0 3 * * * certbot renew --quiet --deploy-hook 'docker-compose -f $SCRIPT_DIR/docker-compose.prod.yml restart nginx'") | crontab -
        echo -e "${GREEN}Auto-renewal configured${NC}"
        ;;
        
    2)
        echo ""
        echo -e "${BLUE}Setting up custom certificates...${NC}"
        echo ""
        echo "You can provide:"
        echo "  - Wildcard certificate (*.cedia.edu.ec)"
        echo "  - Standard certificate for $DOMAIN"
        echo ""
        echo "Certificate files needed:"
        echo "  - Full chain certificate (fullchain.pem or certificate.crt)"
        echo "  - Private key (privkey.pem or private.key)"
        echo ""
        
        # Ask for certificate file path
        read -p "Enter path to full chain certificate file (fullchain.pem or certificate.crt): " CERT_FILE
        if [ ! -f "$CERT_FILE" ]; then
            echo -e "${RED}Error: Certificate file not found: $CERT_FILE${NC}"
            exit 1
        fi
        
        # Ask for private key file path
        read -p "Enter path to private key file (privkey.pem or private.key): " KEY_FILE
        if [ ! -f "$KEY_FILE" ]; then
            echo -e "${RED}Error: Private key file not found: $KEY_FILE${NC}"
            exit 1
        fi
        
        # Copy files
        cp "$CERT_FILE" "$SSL_DIR/fullchain.pem"
        cp "$KEY_FILE" "$SSL_DIR/privkey.pem"
        
        # Set proper permissions
        chmod 644 "$SSL_DIR/fullchain.pem"
        chmod 600 "$SSL_DIR/privkey.pem"
        
        echo -e "${GREEN}Certificates copied to $SSL_DIR${NC}"
        
        # Verify certificate
        echo "Verifying certificate..."
        if openssl x509 -in "$SSL_DIR/fullchain.pem" -text -noout &> /dev/null; then
            echo -e "${GREEN}Certificate is valid${NC}"
            openssl x509 -in "$SSL_DIR/fullchain.pem" -noout -subject -dates
        else
            echo -e "${YELLOW}Warning: Could not verify certificate format${NC}"
        fi
        ;;
        
    3)
        echo "Skipping SSL setup"
        echo -e "${YELLOW}Warning: HTTPS will not work without SSL certificates${NC}"
        exit 0
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Certificate files:"
ls -lh "$SSL_DIR"/*.pem
echo ""
echo "Next steps:"
echo "  1. Restart nginx: docker-compose -f docker-compose.prod.yml restart nginx"
echo "  2. Verify HTTPS: curl -I https://$DOMAIN"
echo ""
