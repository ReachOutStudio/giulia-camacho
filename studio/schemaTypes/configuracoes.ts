import {CogIcon} from '@sanity/icons/Cog'
import {defineField, defineType} from 'sanity'

export const configuracoes = defineType({
  name: 'configuracoes',
  title: 'Configurações',
  type: 'document',
  icon: CogIcon,
  fields: [
    defineField({
      name: 'email',
      title: 'E-mail',
      type: 'string',
      validation: (rule) => rule.required().email(),
    }),
    defineField({
      name: 'whatsapp',
      title: 'WhatsApp',
      type: 'string',
      description: 'Com o código do país. Ex.: +44 7751 022909',
      validation: (rule) => rule.required(),
    }),
    defineField({
      name: 'instagram',
      title: 'Instagram',
      type: 'string',
      description: 'Com @. Ex.: @giuliacamacho_',
    }),
    defineField({
      name: 'base',
      title: 'Cidades (barra lateral)',
      type: 'internationalizedArrayString',
      description: 'Ex.: São Paulo · Londres',
    }),
    defineField({
      name: 'contatoTexto',
      title: 'Frase da página Contato',
      type: 'internationalizedArrayString',
      description: 'Ex.: Baseada em São Paulo. Disponível para trabalhos em Londres.',
    }),
    defineField({
      name: 'descricao',
      title: 'Descrição para o Google',
      type: 'internationalizedArrayText',
      description: 'Uma ou duas frases. Aparece nos resultados de busca e quando o link é compartilhado.',
    }),
  ],
  preview: {prepare: () => ({title: 'Configurações'})},
})
