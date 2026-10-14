import {defineCliConfig} from 'sanity/cli'

export default defineCliConfig({
  api: {
    projectId: '9ybkssyz',
    dataset: 'production'
  },
  studioHost: 'giuliacamacho',
  deployment: {
    appId: 'd5qgrhzcxuxpxf0gzgd0b8xj',
    /**
     * Enable auto-updates for studios.
     * Learn more at https://www.sanity.io/docs/studio/latest-version-of-sanity#k47faf43faf56
     */
    autoUpdates: false,
  },
})
