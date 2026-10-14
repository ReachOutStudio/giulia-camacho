import {HomeIcon} from '@sanity/icons/Home'
import {defineArrayMember, defineField, defineType} from 'sanity'

export const inicio = defineType({
  name: 'inicio',
  title: 'Início',
  type: 'document',
  icon: HomeIcon,
  fields: [
    defineField({
      name: 'destaques',
      title: 'Fotos da página inicial',
      type: 'array',
      description:
        'Aparecem em pares, na ordem da lista. Para cada foto, escolha a série para onde ela leva.',
      of: [
        defineArrayMember({
          type: 'object',
          name: 'destaque',
          title: 'Destaque',
          fields: [
            defineField({
              name: 'foto',
              title: 'Foto',
              type: 'image',
              options: {hotspot: true},
              validation: (rule) => rule.required(),
            }),
            defineField({
              name: 'serie',
              title: 'Leva para a série',
              type: 'reference',
              to: [{type: 'serie'}],
              validation: (rule) => rule.required(),
            }),
          ],
          preview: {
            select: {media: 'foto', title: 'serie.nome'},
            prepare: ({media, title}) => ({media, title: title || 'Escolha a série'}),
          },
        }),
      ],
      validation: (rule) => rule.required().min(2),
    }),
  ],
  preview: {prepare: () => ({title: 'Início'})},
})
