import {ImagesIcon} from '@sanity/icons/Images'
import {defineArrayMember, defineField, defineType} from 'sanity'

export const serie = defineType({
  name: 'serie',
  title: 'Série',
  type: 'document',
  icon: ImagesIcon,
  fields: [
    defineField({
      name: 'nome',
      title: 'Nome da série',
      type: 'string',
      description: 'Ex.: Laís Santana',
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'slug',
      title: 'Endereço no site',
      type: 'slug',
      description: 'Parte final do link da série. Clique em "Gerar" para criar a partir do nome.',
      options: {source: 'nome', maxLength: 60},
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'grupo',
      title: 'Categoria',
      type: 'string',
      options: {
        list: [
          {title: 'Editorial', value: 'editorial'},
          {title: 'Lifestyle', value: 'lifestyle'},
        ],
        layout: 'radio',
        direction: 'horizontal',
      },
      initialValue: 'editorial',
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'ordem',
      title: 'Ordem no menu',
      type: 'number',
      description: 'Números menores aparecem primeiro.',
      initialValue: 10,
    }),
    defineField({
      name: 'lugar',
      title: 'Lugar',
      type: 'internationalizedArrayString',
      description: 'Ex.: City de Londres / City of London',
    }),
    defineField({
      name: 'texto',
      title: 'Texto da série',
      type: 'internationalizedArrayText',
      description: 'Duas ou três linhas sobre a série.',
    }),
    defineField({
      name: 'creditos',
      title: 'Créditos',
      type: 'string',
      description: 'Opcional. Ex.: Styling: Ana Lima · Beleza: Bia Souza',
    }),
    defineField({
      name: 'capa',
      title: 'Foto de capa',
      type: 'image',
      description: 'Aparece no índice da categoria (Editorial ou Lifestyle).',
      options: {hotspot: true},
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'fotos',
      title: 'Fotos',
      type: 'array',
      description: 'Arraste as fotos para mudar a ordem. No site, elas aparecem em pares.',
      of: [defineArrayMember({type: 'image', options: {hotspot: true}})],
      options: {layout: 'grid'},
      validation: (rule) => rule.required().min(1),
    }),
  ],
  orderings: [
    {
      title: 'Ordem no menu',
      name: 'ordemMenu',
      by: [
        {field: 'grupo', direction: 'asc'},
        {field: 'ordem', direction: 'asc'},
      ],
    },
  ],
  preview: {
    select: {title: 'nome', grupo: 'grupo', media: 'capa'},
    prepare: ({title, grupo, media}) => ({
      title,
      subtitle: grupo === 'lifestyle' ? 'Lifestyle' : 'Editorial',
      media,
    }),
  },
})
