import {ptBRLocale} from '@sanity/locale-pt-br'
import {defineConfig} from 'sanity'
import {internationalizedArray} from 'sanity-plugin-internationalized-array'
import {structureTool} from 'sanity/structure'
import {schemaTypes} from './schemaTypes'
import {SINGLETONS, structure} from './structure'

export default defineConfig({
  name: 'default',
  title: 'Giulia Camacho',

  projectId: '9ybkssyz',
  dataset: 'production',

  plugins: [
    structureTool({structure}),
    internationalizedArray({
      languages: [
        {id: 'pt', title: 'Português'},
        {id: 'en', title: 'English'},
      ],
      defaultLanguages: ['pt', 'en'],
      fieldTypes: ['string', 'text'],
      languageDisplay: 'titleOnly',
    }),
    ptBRLocale(),
  ],

  schema: {
    types: schemaTypes,
    templates: (templates) => [
      ...templates.filter(({schemaType}) => !SINGLETONS.includes(schemaType)),
      {
        id: 'serie-editorial',
        title: 'Série editorial',
        schemaType: 'serie',
        value: {grupo: 'editorial'},
      },
      {
        id: 'serie-lifestyle',
        title: 'Série lifestyle',
        schemaType: 'serie',
        value: {grupo: 'lifestyle'},
      },
    ],
  },

  document: {
    // Início, Sobre e Configurações são páginas únicas: não podem ser duplicadas nem apagadas.
    actions: (input, context) =>
      SINGLETONS.includes(context.schemaType)
        ? input.filter(({action}) => action && ['publish', 'discardChanges', 'restore'].includes(action))
        : input,
    newDocumentOptions: (prev) =>
      prev.filter((item) => !SINGLETONS.includes(item.templateId)),
  },
})
