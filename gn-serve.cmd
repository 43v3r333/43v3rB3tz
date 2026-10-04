@echo off
cd /d C:\Users\p3rc\Desktop\dev\ProphitBet-Soccer-Bets-Predictor
set GITNEXUS_SKIP_OPTIONAL_GRAMMARS=1
pnpm --allow-build=@ladybugdb/core --allow-build=gitnexus --allow-build=tree-sitter dlx gitnexus@latest serve > "%TEMP%\gitnexus-serve.log" 2>&1
