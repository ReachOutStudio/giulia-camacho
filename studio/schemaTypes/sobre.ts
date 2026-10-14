import {UserIcon} from '@sanity/icons/User'
import {defineArrayMember, defineField, defineType} from 'sanity'

export const sobre = defineType({
  name: 'sobre',
  title: 'Sobre',
  type: 'document',
  icon: UserIcon,
  fields: [
    defineField({
      name: 'retrato',
      title: 'Retrato da Giulia',
      type: 'image',
      options: {hotspot: true},
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'bio',
      title: 'Bio',
      type: 'internationalizedArrayText',
      description: 'Deixe uma linha em branco entre um parágrafo e outro.',
    }),
    defineField({
      name: 'linhaDoTempo',
      title: 'Linha do tempo',
      type: 'array',
      of: [
        defineArrayMember({
          type: 'object',
          name: 'etapa',
          title: 'Etapa',
          fields: [
            defineField({name: 'lugar', title: 'Lugar', type: 'internationalizedArrayString'}),
            defineField({name: 'descricao', title: 'Descrição', type: 'internationalizedArrayString'}),
          ],
          preview: {
            select: {lugar: 'lugar', descricao: 'descricao'},
            prepare: ({lugar, descricao}) => ({
              title: lugar?.[0]?.value || 'Etapa',
              subtitle: descricao?.[0]?.value,
            }),
          },
        }),
      ],
    }),
  ],
  preview: {prepare: () => ({title: 'Sobre'})},
})
