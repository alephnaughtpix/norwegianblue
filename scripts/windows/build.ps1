# Regenerate tags & categories, then run full build.

cd "../.."
#bundle exec jekyll build --config _config.yml,_config.dev.yml
bundle exec jekyll build --verbose --config _config.yml,_config.dev.yml
cd .\scripts\windows\
