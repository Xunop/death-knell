# death-knell
一个查成绩的脚本，希望接收到的不是噩耗...

## Note

Just for NJUPT.

## What's this?

一个查询成绩（平时成绩/卷面分）并将结果通过 webhook 发送出去。

平时成绩和卷面分的查询有些随机... 我目前不知道如何解决。

## How to Use it

查看 `run-example.sh` 脚本内容，修改参数。

如果你使用 Linux, 那么可以配合 systemd timer 设置定时任务，定时查询并将更新的成绩发送出去。
