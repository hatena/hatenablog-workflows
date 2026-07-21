# scripts

## update-revision.bash

hatena/hatenablog-workflowsのGitHub Actionsを自己参照している箇所のリビジョンを更新するスクリプトで、hatena/hatenablog-workflows開発用のファイルです。

新しいリリースを打つ前に、手元のgitリポジトリを最新にして `./scripts/update-revision.bash` を実行したあと、`update-hatenablog-workflows-digest` ブランチの内容をmainに（Pull Request経由で）取り込んでください
