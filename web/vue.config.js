const deployment = require('./deploy/config.json');

module.exports = {
  publicPath: process.env.VUE_APP_ASSET_BASE || './',
  productionSourceMap: false,
  transpileDependencies: ['vuetify'],
  chainWebpack(config) {
    config.plugin('html').tap(args => {
      args[0].localAssetPrefix = deployment.localAssetPrefix;
      return args;
    });
  }
}
