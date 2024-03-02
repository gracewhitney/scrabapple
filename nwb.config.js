const path = require('path')
const BundleTracker = require('webpack-bundle-tracker')


/**
 * Entry point configuration.
 *
 * This is where you should configure your webpack entry points, for example, a different entry point per page.
 */

const ENTRIES = {
  TileRack: './src/Components/TileRack.js',
  ScrabbleGame: './src/Pages/ScrabbleGame.js',
  UpwordsGame: './src/Pages/UpwordsGame.js',
}

const SHARED_ENTRIES = []

/**
 * nwb config
 */
module.exports = function({command}) {

  /* Set config */
  const config = {
    type: 'react-app',
  }
  config.webpack = {
    config(webpackConfig) {

      // Set new entry configuration
      webpackConfig.entry = {}
      Object.keys(ENTRIES).forEach((entryKey) => {
        webpackConfig.entry[entryKey] = [...SHARED_ENTRIES, ENTRIES[entryKey]]
      })
      return webpackConfig
    },
    extra: {
      output: {
        filename: '[name].js',
        chunkFilename: '[name].js',
        path: path.resolve('./static/webpack_bundles/'),
      },
      module: {
        rules: [
          {
            test: /\.js$/,
            exclude: /node_modules/,
            loader: 'django-react-loader',
          },
          {
            test: /dnd/,
            loader: 'babel-loader',
            options: {
              babelrc: false,
              cacheDirectory: true,
              plugins: [
                "@babel/plugin-transform-nullish-coalescing-operator",
                "@babel/plugin-transform-optional-chaining"
              ],
              presets: [
                ['@babel/preset-env', { targets: "defaults" }]
              ]
            }
          }
        ],
      },
      plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
      ],
    },
    publicPath: '/static/webpack_bundles/',
  }
  config.babel = {
    plugins: "@babel/plugin-transform-nullish-coalescing-operator",
  }
  return config
}
