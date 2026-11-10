from api.schemas.enums import NiveisAcessoEnum
from api.schemas.global_schemas import UsuarioLogado


def is_admin_or_master(user: UsuarioLogado) -> bool:
    return user.niveis_acesso_id in {
        NiveisAcessoEnum.ADMINISTRADOR.value,
        NiveisAcessoEnum.MASTER.value,
    }


def is_master(user: UsuarioLogado) -> bool:
    return user.niveis_acesso_id == NiveisAcessoEnum.MASTER.value
