import enum

from sqlalchemy import Enum


class DeclarationEnum(enum.Enum):
    initial = 'I'
    modification = 'M'
    conclusion = 'C'


decl_type_mapper_es = {
    'INICIAL': DeclarationEnum.initial.value,
    'MODIFICACIÓN': DeclarationEnum.modification.value,
    'CONCLUSIÓN': DeclarationEnum.conclusion.value
}


DeclarationType = Enum(*(e.value for e in DeclarationEnum))

