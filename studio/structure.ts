import {CogIcon} from '@sanity/icons/Cog'
import {HomeIcon} from '@sanity/icons/Home'
import {ImagesIcon} from '@sanity/icons/Images'
import {UserIcon} from '@sanity/icons/User'
import type {StructureResolver} from 'sanity/structure'

export const SINGLETONS = ['inicio', 'sobre', 'configuracoes']

export const structure: StructureResolver = (S) =>
  S.list()
    .title('Site da Giulia')
    .items([
      S.listItem()
        .title('Início')
        .icon(HomeIcon)
        .child(S.document().schemaType('inicio').documentId('inicio').title('Início')),
      S.listItem()
        .title('Sobre')
        .icon(UserIcon)
        .child(S.document().schemaType('sobre').documentId('sobre').title('Sobre')),
      S.listItem()
        .title('Configurações')
        .icon(CogIcon)
        .child(
          S.document().schemaType('configuracoes').documentId('configuracoes').title('Configurações'),
        ),
      S.divider(),
      S.listItem()
        .title('Editorial')
        .icon(ImagesIcon)
        .child(
          S.documentList()
            .title('Editorial')
            .schemaType('serie')
            .filter('_type == "serie" && grupo == "editorial"')
            .defaultOrdering([{field: 'ordem', direction: 'asc'}])
            .initialValueTemplates([S.initialValueTemplateItem('serie-editorial')]),
        ),
      S.listItem()
        .title('Lifestyle')
        .icon(ImagesIcon)
        .child(
          S.documentList()
            .title('Lifestyle')
            .schemaType('serie')
            .filter('_type == "serie" && grupo == "lifestyle"')
            .defaultOrdering([{field: 'ordem', direction: 'asc'}])
            .initialValueTemplates([S.initialValueTemplateItem('serie-lifestyle')]),
        ),
    ])
