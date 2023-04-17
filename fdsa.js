inputAST = {
    "parent": "PROG",
    "id": "1",
    "children": [
        {
            "parent": "ALGO",
            "id": "2",
            "children": [
                {
                    "parent": "ALGO",
                    "id": "5",
                    "children": []
                },
                {
                    "parent": "ALGO",
                    "id": "6",
                    "children": []
                },
                {
                    "parent": "ALGO",
                    "id": "4",
                    "children": []
                }
            ]
        },
        {
            "parent": "PROCDEFS",
            "id": "3",
            "children": []
        }
    ]
}

outputAST = {
    'PROG-1': {
        '@id': '1',
        '@children': '2,3',

        'ALGO-2': {
            '@id': '2',
            '@children': '4,5,6',

            'INSTRS-4': {
                '@id': '4',
                '@children': ''
            },

            'INSTRS-5': {
                '@id': '5',
                '@children': ''
            },

            'INSTRS-6': {
                '@id': '6',
                '@children': ''
            }
        },

        'PROCDEFS': {
            '@id': '3',
            '@children': ''
        }
    }
}