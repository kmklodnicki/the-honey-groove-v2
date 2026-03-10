import { Helmet } from 'react-helmet-async';

const SITE_NAME = 'The Honey Groove';
const SITE_URL = 'https://thehoneygroove.com';
const DEFAULT_IMAGE = `${SITE_URL}/og-image.png`;
const DEFAULT_DESC = 'The vinyl social club, finally. Track your collection, discover pressings, and connect with collectors worldwide.';

/**
 * SEOHead — Dynamic metadata component for all page types.
 *
 * Props:
 *  - title: Page title (will be appended with site name)
 *  - description: Meta description
 *  - image: OG image URL
 *  - url: Canonical URL path (e.g. "/profile/username")
 *  - type: OG type (website, product, profile, article, music.song)
 *  - jsonLd: JSON-LD structured data object
 *  - vinylMeta: { artist, album, variant, color, year, label, catno, format, rpm, discCount, pressingCountry }
 *  - productMeta: { price, currency, availability, condition }
 *  - tradeMeta: { available, iso, tradeType, negotiable }
 *  - conditionMeta: { mediaCondition, sleeveCondition, graded }
 *  - postMeta: { type, artist, album, variant }
 *  - collectorMeta: { username, collectionSize, isoCount }
 *  - noIndex: boolean — prevent indexing (for private pages)
 */
const SEOHead = ({
  title,
  description,
  image,
  url,
  type = 'website',
  jsonLd,
  vinylMeta,
  productMeta,
  tradeMeta,
  conditionMeta,
  postMeta,
  collectorMeta,
  noIndex = false,
}) => {
  const fullTitle = title ? `${title} | ${SITE_NAME}` : SITE_NAME;
  const fullUrl = url ? (url.startsWith('http') ? url : `${SITE_URL}${url}`) : SITE_URL;
  const desc = description || DEFAULT_DESC;
  const img = image || DEFAULT_IMAGE;

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <link rel="canonical" href={fullUrl} />
      {noIndex && <meta name="robots" content="noindex, nofollow" />}

      {/* Open Graph */}
      <meta property="og:site_name" content={SITE_NAME} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      <meta property="og:image" content={img} />
      <meta property="og:url" content={fullUrl} />
      <meta property="og:type" content={type} />

      {/* Twitter Card */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={desc} />
      <meta name="twitter:image" content={img} />

      {/* Vinyl-specific metadata */}
      {vinylMeta?.artist && <meta name="vinyl:artist" content={vinylMeta.artist} />}
      {vinylMeta?.album && <meta name="vinyl:album" content={vinylMeta.album} />}
      {vinylMeta?.variant && <meta name="vinyl:variant" content={vinylMeta.variant} />}
      {vinylMeta?.color && <meta name="vinyl:color" content={vinylMeta.color} />}
      {vinylMeta?.year && <meta name="vinyl:release_year" content={String(vinylMeta.year)} />}
      {vinylMeta?.label && <meta name="vinyl:label" content={vinylMeta.label} />}
      {vinylMeta?.catno && <meta name="vinyl:catalog_number" content={vinylMeta.catno} />}
      {vinylMeta?.format && <meta name="vinyl:format" content={vinylMeta.format} />}
      {vinylMeta?.rpm && <meta name="vinyl:speed" content={vinylMeta.rpm} />}
      {vinylMeta?.discCount && <meta name="vinyl:disc_count" content={String(vinylMeta.discCount)} />}
      {vinylMeta?.pressingCountry && <meta name="vinyl:pressing_country" content={vinylMeta.pressingCountry} />}

      {/* Product/marketplace metadata */}
      {productMeta?.price && <meta property="product:price:amount" content={String(productMeta.price)} />}
      {productMeta?.price && <meta property="product:price:currency" content={productMeta.currency || 'USD'} />}
      {productMeta?.availability && <meta property="product:availability" content={productMeta.availability} />}
      {productMeta?.condition && <meta property="product:condition" content={productMeta.condition} />}

      {/* Condition metadata */}
      {conditionMeta?.mediaCondition && <meta name="vinyl:media_condition" content={conditionMeta.mediaCondition} />}
      {conditionMeta?.sleeveCondition && <meta name="vinyl:sleeve_condition" content={conditionMeta.sleeveCondition} />}
      {conditionMeta?.graded !== undefined && <meta name="vinyl:graded" content={String(conditionMeta.graded)} />}

      {/* Trade metadata */}
      {tradeMeta?.available && <meta name="trade:available" content="true" />}
      {tradeMeta?.iso && <meta name="trade:iso" content={tradeMeta.iso} />}
      {tradeMeta?.tradeType && <meta name="trade:trade_type" content={tradeMeta.tradeType} />}
      {tradeMeta?.negotiable !== undefined && <meta name="trade:negotiable" content={String(tradeMeta.negotiable)} />}

      {/* Post metadata */}
      {postMeta && <meta name="post:type" content="vinyl" />}
      {postMeta?.artist && <meta name="post:artist" content={postMeta.artist} />}
      {postMeta?.album && <meta name="post:album" content={postMeta.album} />}
      {postMeta?.variant && <meta name="post:variant" content={postMeta.variant} />}

      {/* Collector metadata */}
      {collectorMeta?.username && <meta name="collector:username" content={collectorMeta.username} />}
      {collectorMeta?.collectionSize !== undefined && <meta name="collector:collection_size" content={String(collectorMeta.collectionSize)} />}
      {collectorMeta?.isoCount !== undefined && <meta name="collector:iso_count" content={String(collectorMeta.isoCount)} />}

      {/* JSON-LD Structured Data */}
      {jsonLd && (
        <script type="application/ld+json">
          {JSON.stringify(jsonLd)}
        </script>
      )}
    </Helmet>
  );
};

export default SEOHead;
