const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  publicPath: '/vueapp/',
  configureWebpack: {
    entry: "./src/main.js",
    devServer: {
      hot: true,
      port: 8080,
      host: '0.0.0.0',
    },
    watch: true,
    watchOptions: {
      ignored: /node_modules/,
      poll: 1000
    }

  }
})
