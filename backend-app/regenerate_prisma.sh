#!/bin/bash

# Regenerate Prisma client after schema changes
echo "Regenerating Prisma client..."

# Push schema changes to database
npx prisma db push

# Generate Prisma client
npx prisma generate

echo "Prisma client regenerated successfully!"