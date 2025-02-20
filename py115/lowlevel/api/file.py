__author__ = 'deadblue'

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, Sequence

from py115.compat import StrEnum
from py115.lowlevel.protocol import RetryException
from ._base import JsonApiSpec, JsonResult, VoidApiSpec
from ._util import to_timestamp


@dataclass(init=False)
class FileObject:
    """
    FileObject represents a file/directory item in cloud storage.
    """

    file_id: str
    """Unique ID of the file/directory."""

    parent_id: str
    """File ID of parent directory."""

    name: str
    """Base name."""

    pickcode: str
    """Pick code for download/play."""

    is_dir: bool
    """Indicate whether file is a directory."""

    is_hidden: bool
    """Indicate whether file is hidden."""

    size: int = 0
    """File size in bytes."""

    sha1: Optional[str] = None
    """File SHA-1 hash in HEX-format."""

    update_time: int
    """Timestamp when file is updated."""

    create_time: Optional[int] = None
    """Timestamp when file is created."""

    open_time: Optional[int] = None
    """Timestamp when file is opened."""

    is_video: bool = False
    """Indicate whether file is video."""

    media_duration: Optional[int] = None
    """Media duration in seconds for audio/video file."""

    video_definition: Optional[int] = None
    """Video definition for video file."""

    def __new__(cls, json_obj: JsonResult):
        ret = object.__new__(cls)
        ret.is_dir = 'fid' not in json_obj
        ret.name = json_obj['n']
        ret.pickcode = json_obj['pc']
        ret.is_hidden = json_obj['hdf'] != 0
        if 'te' in json_obj:
            ret.update_time = to_timestamp(json_obj['te'])
        elif 'tu' in json_obj:
            ret.update_time = to_timestamp(json_obj['tu'])
        if 'tp' in json_obj:
            ret.create_time = to_timestamp(json_obj['tp'])
        if 'to' in json_obj:
            ret.open_time = to_timestamp(json_obj['to'])
        if ret.is_dir:
            ret.file_id = json_obj['cid']
            ret.parent_id = json_obj['pid']
        else:
            ret.file_id = json_obj['fid']
            ret.parent_id = json_obj['cid']
            ret.size = json_obj['s']
            ret.sha1 = json_obj['sha']
            ret.is_video = json_obj.get('iv', 0) == 1
            ret.media_duration = json_obj.get('play_long', None)
            ret.video_definition = json_obj.get('vdi', None)
        return ret


@dataclass
class FileListResult:

    files: List[FileObject]
    order_mode: str
    order_asc: int
    offset: int
    limit: int
    count: int


class FileListApi(JsonApiSpec[FileListResult]):

    def __init__(self, dir_id: str, offset: int = 0, limit: int = 115) -> None:
        super().__init__('')
        self.query.update({
            'aid': '1',
            'cid': dir_id,
            'show_dir': '1',
            'o': 'user_ptime',
            'asc': '1',
            'offset': str(offset),
            'limit': str(limit),
            'fc_mix': '0',
            'natsort': '1',
            'format': 'json'
        })

    def url(self) -> str:
        order_mode = self.query.get('o', 'user_ptime')
        if order_mode == 'file_name':
            return 'https://aps.115.com/natsort/files.php'
        else:
            return 'https://webapi.115.com/files'
    
    def _get_error_code(self, json_obj: JsonResult) -> int:
        err_code = super()._get_error_code(json_obj)
        if err_code == 20130827:
            self.query.update({
                'o': json_obj.get('order'),
                'asc': str(json_obj.get('is_asc'))
            })
            raise RetryException()
        return err_code

    def _parse_json_result(self, obj: JsonResult) -> FileListResult:
        ret = FileListResult(
            files=[],
            order_mode=obj.get('order'),
            order_asc=obj.get('is_ac'),
            offset=obj.get('offset'),
            limit=obj.get('limit'),
            count=obj.get('count')
        )
        for file_obj in obj['data']:
            ret.files.append(FileObject(file_obj))
        return ret
    
    def set_offset(self, value: int):
        self.query['offset'] = str(value)



class FileSearchApi(JsonApiSpec[FileListResult]):

    def __init__(
            self, 
            keyword: str, 
            dir_id: str = '0', 
            offset: int = 0, 
            limit: int = 115
        ) -> None:
        super().__init__('https://webapi.115.com/files/search')
        self.query.update({
            'aid': '1',
            'cid': dir_id,
            'search_value': keyword,
            'offset': str(offset),
            'limit': str(limit),
            'format': 'json'
        })
    
    def _parse_json_result(self, json_obj: JsonResult) -> FileListResult:
        ret = FileListResult(
            files=[],
            order_mode=json_obj.get('order'),
            order_asc=json_obj.get('is_ac'),
            offset=json_obj.get('offset'),
            limit=json_obj.get('page_size'),
            count=json_obj.get('count')
        )
        for file_obj in json_obj['data']:
            ret.files.append(FileObject(file_obj))
        return ret

    def set_offset(self, value: int):
        self.query['offset'] = str(value)


@dataclass
class PathNode:

    file_id: str
    name: str


@dataclass
class FileGetResult:

    name: str
    pickcode: str
    is_dir: bool
    path: List[PathNode]


class FileGetApi(JsonApiSpec[FileGetResult]):

    def __init__(self, file_id: str) -> None:
        super().__init__('https://webapi.115.com/category/get')
        self.query['cid'] = file_id
    
    def _parse_json_result(self, json_obj: JsonResult) -> FileGetResult:
        return super()._parse_json_result(json_obj)
    


class FileDeleteApi(VoidApiSpec):

    def __init__(self, file_ids: Sequence[str]) -> None:
        super().__init__('https://webapi.115.com/rb/delete')
        for index, file_id in enumerate(file_ids):
            sub_key = f'fid[{index}]'
            self.form[sub_key] = file_id
        self.form['ignore_warn'] = '1'


class FileMoveApi(VoidApiSpec):

    def __init__(self, target_dir_id: str, file_ids: Sequence[str]) -> None:
        super().__init__('https://webapi.115.com/files/move')
        self.form['pid'] = target_dir_id
        for index, file_id in enumerate(file_ids):
            sub_key = f'fid[{index}]'
            self.form[sub_key] = file_id
        self.form['ignore_warn'] = '1'


class FileRenameApi(VoidApiSpec):

    def __init__(self, new_names: Dict[str, str]) -> None:
        super().__init__('https://webapi.115.com/files/batch_rename')
        for file_id, new_name in new_names.items():
            key = f'files_new_name[{file_id}]'
            self.form[key] = new_name


class DirAddApi(JsonApiSpec[str]):

    def __init__(self, parent_id: str, dir_name: str) -> None:
        super().__init__(
            api_url='https://webapi.115.com/files/add'
        )
        self.form.update({
            'pid': parent_id,
            'cname': dir_name
        })

    def _parse_json_result(self, json_obj: JsonResult) -> str:
        return json_obj.get('file_id')


class DirOrder(StrEnum):
    """
    Mode to sort files in directory.
    """

    FILE_NAME = 'file_name'
    """Sort files by name."""

    FILE_SIZE = 'file_size'
    """Sort files by size."""

    FILE_TYPE = 'file_type'
    """Sort files by type."""

    CREATE_TIME = 'user_ptime'
    """Sort files by created time."""

    UPDATE_TIME = 'user_utime'
    """Sort files by last updated name."""

    OPEN_TIME = 'user_otime'
    """Sort files by last opened time."""


class DirSortApi(VoidApiSpec):

    def __init__(self, dir_id: str, order: DirOrder, is_asc: bool) -> None:
        super().__init__(
            api_url='https://webapi.115.com/files/order'
        )
        self.form.update({
            'file_id': dir_id,
            'user_order': order.value,
            'user_asc': '1' if is_asc else '0',
            'fc_mix': 0
        })


@dataclass
class SpaceInfoResult:

    total_size: float
    remain_size: float
    used_size: float


class SpaceInfoApi(JsonApiSpec[SpaceInfoResult]):

    def __init__(self) -> None:
        super().__init__('https://webapi.115.com/files/index_info')

    def _parse_json_result(self, json_obj: JsonResult) -> SpaceInfoResult:
        space_info_obj = json_obj['data']['space_info']
        return SpaceInfoResult(
            total_size=space_info_obj['all_total']['size'],
            remain_size=space_info_obj['all_remain']['size'],
            used_size=space_info_obj['all_use']['size'],
        )
