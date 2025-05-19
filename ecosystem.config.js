module.exports = {
  apps: [{
    name: 'lolz-auto-buyer',
    script: '/usr/bin/python3.10',
    args: '-m src',
    watch: false,
    autorestart: true,
    max_restarts: 10,
    restart_delay: 4000,
    env: {
      NODE_ENV: 'production'
    }
  }]
} 