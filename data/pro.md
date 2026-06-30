## matrix-final-data

```json
{
    "id": 29470, 
    "num": 14,
    "height": 3,
    "img": "mat_333_29470.png",
    "mat": [[3, 2, 1], [0, 0, 2], [3, 1, 2]],
    "f_mat": [[1, 0, 0], [1, 1, 1], [1, 1, 1]],
    "r_mat": [[1, 0, 1], [1, 1, 1], [1, 1, 1]],
    "t_mat": [[1, 1, 1], [0, 0, 1], [1, 1, 1]],
    "diff": "难",
    "restorable": [29461, 29462, 29470, 29471]
}
```
```python
# id: 该格式下唯一标识
# num: 总方块个数
# height: 最大堆叠高度
# img: 对应图片名称
# mat: 原始矩阵
# f_mat: 正视图
# r_mat: 右视图
# t_mat: 俯视图
# diff: 难易度初划分
# restorable: 三视图对应一致的组
```
```python
# 注: 
# 左视图可由 l_mat = [row[::-1] for row in r_mat] 或 np.fliplr(r_mat)
# len(item["restorable"]) == 1 表示该立体图在满足唯一对应情况下可由三视图还原
```