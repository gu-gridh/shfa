[<Q: (AND: 
    (OR: ('keywords__text__icontains', 'aram'), ('keywords__english_translation__icontains', 'aram')), 
    (OR: ('keywords__text__icontains', 'mrzk'), ('keywords__english_translation__icontains', 'mrzk'))
)>]


['aram', 'mrzk']
[<Q: 
 (AND: 
  (OR: ('keywords__text__icontains', 'aram'), ('keywords__english_translation__icontains', 'aram')), 
  (OR: ('keywords__text__icontains', 'mrzk'), ('keywords__english_translation__icontains', 'mrzk')))
  >]
(AND: 
 (AND: 
  (OR: ('keywords__text__icontains', 'aram'), ('keywords__english_translation__icontains', 'aram')), 
  (OR: ('keywords__text__icontains', 'mrzk'), ('keywords__english_translation__icontains', 'mrzk')))
  )

['aram', 'mrzk']
[
    <Q: (OR: ('site__raa_id__icontains', 'tanum'), ('site__lamning_id__icontains', 'tanum'))>, 
    <Q: (AND: 
        (OR: ('keywords__text__icontains', 'aram'), ('keywords__english_translation__icontains', 'aram')), 
        (OR: ('keywords__text__icontains', 'mrzk'), ('keywords__english_translation__icontains', 'mrzk')
        ))>
]

(AND: 
    (OR: ('site__raa_id__icontains', 'tanum'), ('site__lamning_id__icontains', 'tanum')),
    (AND: 
        (OR: ('keywords__text__icontains', 'aram'), ('keywords__english_translation__icontains', 'aram')), 
        (OR: ('keywords__text__icontains', 'mrzk'), ('keywords__english_translation__icontains', 'mrzk'))
    )
)
