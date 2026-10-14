// Importa o conteúdo atual do site (séries, fotos, Sobre, Início e Configurações) para o Sanity.
// Uso: PAYLOAD=/caminho/import-payload.json npx sanity exec scripts/importar.mjs --with-user-token
import {createReadStream, readFileSync} from 'node:fs'
import {basename} from 'node:path'
import {randomUUID} from 'node:crypto'
import {getCliClient} from 'sanity/cli'

const client = getCliClient({apiVersion: '2025-02-19'})
const data = JSON.parse(readFileSync(process.env.PAYLOAD, 'utf8'))
const key = () => randomUUID().replace(/-/g, '').slice(0, 12)

const intl = (obj, kind) =>
  ['pt', 'en']
    .filter((lang) => obj?.[lang])
    .map((lang) => ({
      _key: key(),
      _type: `internationalizedArray${kind}Value`,
      language: lang,
      value: obj[lang],
    }))

const assets = new Map()
async function upload(path) {
  if (!assets.has(path)) {
    const doc = await client.assets.upload('image', createReadStream(path), {filename: basename(path)})
    assets.set(path, doc._id)
    process.stdout.write('.')
  }
  return assets.get(path)
}
const image = async (path, withKey = false) => ({
  ...(withKey ? {_key: key()} : {}),
  _type: 'image',
  asset: {_type: 'reference', _ref: await upload(path)},
})

const existing = await client.fetch('count(*[_type == "serie"])')
if (existing > 0) {
  console.error(`Já existem ${existing} séries no dataset. Nada foi importado.`)
  process.exit(1)
}

const ids = {}
for (const s of data.series) {
  const fotos = []
  for (const p of s.fotos) fotos.push(await image(p, true))
  const doc = await client.create({
    _type: 'serie',
    nome: s.nome,
    slug: {_type: 'slug', current: s.slug},
    grupo: s.grupo,
    ordem: s.ordem,
    lugar: intl(s.lugar, 'String'),
    texto: intl(s.texto, 'Text'),
    capa: await image(s.capa),
    fotos,
  })
  ids[s.slug] = doc._id
  console.log(`\nSérie: ${s.nome} (${fotos.length} fotos)`)
}

const destaques = []
for (const d of data.home) {
  destaques.push({
    _key: key(),
    _type: 'destaque',
    foto: await image(d.foto),
    serie: {_type: 'reference', _ref: ids[d.serie]},
  })
}

const tx = client.transaction()
tx.createOrReplace({_id: 'inicio', _type: 'inicio', destaques})
tx.createOrReplace({
  _id: 'sobre',
  _type: 'sobre',
  retrato: await image(data.sobre.retrato),
  bio: intl(data.sobre.bio, 'Text'),
  linhaDoTempo: data.sobre.linha.map((e) => ({
    _key: key(),
    _type: 'etapa',
    lugar: intl(e.lugar, 'String'),
    descricao: intl(e.descricao, 'String'),
  })),
})
tx.createOrReplace({
  _id: 'configuracoes',
  _type: 'configuracoes',
  email: data.config.email,
  whatsapp: data.config.whatsapp,
  instagram: data.config.instagram,
  base: intl(data.config.base, 'String'),
  contatoTexto: intl(data.config.contatoTexto, 'String'),
  descricao: intl(data.config.descricao, 'Text'),
})
await tx.commit()

console.log(`\nPronto: ${data.series.length} séries, ${assets.size} imagens, Início, Sobre e Configurações.`)
