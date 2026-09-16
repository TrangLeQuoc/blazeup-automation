# Công cụ đối chiếu backend — nơi lưu kết quả

Bốn công cụ đọc source backend (`blazeupai/blazeup-microservice-sa-partners`) rồi đối chiếu
với bộ test này. Mỗi lần chạy đều lưu kết quả vào đây kèm ngày giờ, nên thư mục này là một
**lịch sử** chứ không phải một file luôn-mới-nhất — vì *"con số đó đổi từ lúc nào"* là câu
hỏi mà sau đó không cách nào trả lời được.

Chạy cả bốn từ **repo automation**, không phải từ clone backend: chúng là module ở đây và
cần `api_clients/` cùng `runner/tc_registry` để gọi tên TC. Clone backend chỉ là **đầu vào**
và không bao giờ bị ghi.

```
BLAZEUP_BE_REPO="C:/Users/you/Desktop/blazeup/blazeup-microservice-sa-partners"
```

Đặt một lần trong `config/blazeup/.env` (biến môi trường cùng tên sẽ ghi đè).

---

## Trước mỗi lần chạy: pull clone

Cả bốn đều đọc **file trên đĩa**, mà file đi theo `HEAD` của clone. `HEAD` chỉ nhích khi
`git pull` — `git fetch` chỉ cập nhật `origin/<branch>`, còn `HEAD` và file trên đĩa **không
đổi**. Nên clone chưa pull khiến cả bốn báo cáo trên source của hôm qua.

```powershell
cd <đường dẫn trong BLAZEUP_BE_REPO>; git pull
```

Thay bằng đường dẫn của bạn — một chuỗi trông thật như `C:\Users\you\...` chỉ khiến người đọc
paste thẳng rồi lỗi. Dùng `;` chứ không `&&`: Windows PowerShell 5.1 không có `&&`, nó báo
parser error.

**Pull một lần là đủ cho cả bốn** — chúng đọc cùng một clone. Không cần pull lại giữa các
lệnh, trừ khi BE vừa merge thêm trong lúc bạn đang chạy.

`be_drift` là cái sai **âm thầm**: clone cũ thì không có gì để diff, nên nó in
`No source changes since the baseline. Nothing to re-run.` — **an toàn giả**, không phải lỗi.
Ba cái kia in commit đang đọc, nên ngày cũ là nhìn thấy được.

### Cảnh báo

Cả bốn đều in một dòng khi clone đi sau upstream:

```
Backend : v26 @ 284ce5e (2026-08-07)
WARNING: origin/v26 has 6 commits this clone does not — `git pull` it and re-run, or you are reading stale source
```

Với `be_coverage` dòng này còn nằm **trong map**, vì map dựng từ clone cũ thì sai suốt đời file
đó, còn dòng console thì trôi mất sau một phút. Với `be_drift` nó in **phía trên** dòng
all-clear, cộng một dòng nữa phủ định dòng đó. Với `be_test_blame --run` nó in **trước khi**
jest chạy, để bạn không mất hai phút cho source mà một lệnh pull sắp thay.

Nó đọc remote-tracking ref **đúng như đang có**: không cần mạng, không ghi gì vào clone. Điểm
hở là `origin/<branch>` cũng chỉ mới bằng lần fetch gần nhất của bạn — thêm `--check-remote`
vào bất kỳ lệnh nào trong bốn để `git fetch` trước (~3 giây, vẫn không đụng `HEAD`).

Bốn tool này **cố ý không bao giờ tự pull**. Cờ `--pull` là cách sửa dễ thấy nhất và đã bị
loại: nó nhích `HEAD` của bạn như tác dụng phụ của một câu hỏi chỉ-đọc, và phá lời hứa rằng
clone chỉ là đầu vào.

## Thứ tự chạy sau khi pull

| Thứ tự | Lệnh | Trả lời |
|---|---|---|
| 1 | `python -m utils.be_drift` | BE đổi gì → TC nào chạy lại |
| 2 | `python -m utils.be_coverage` | endpoint nào không ai test |
| 3 | `python -m utils.be_unit_audit` | unit test BE có bảo vệ được gì |
| 4 | `python -m utils.be_test_blame --run` | test BE đỏ vì ai, commit nào (~2 phút) |

`be_drift` đi đầu vì nó là cái duy nhất mà output cũ đọc ra thành tin vui, và vì câu trả lời
của nó — *cái gì đã đổi* — quyết định ba cái sau hôm nay có đáng chạy không.
`be_test_blame --run` đi cuối: chỉ nó tốn tới đơn vị phút.

---

## 1. `python -m utils.be_coverage`

**Câu hỏi** — endpoint nào của backend có ai test?

**Cách hoạt động** — trích mọi route `@Get`/`@Post`/… từ controller backend, trích mọi
endpoint mà `api_clients/` của bộ test này thật sự gọi, rồi nối hai bên theo method + path.
Một route được coi là có unit test **chỉ khi** một spec có nhắc **tên class** controller đó
đồng thời nhắc cả tên handler.

| | |
|---|---|
| Input | backend `src/**/*.controller.ts` + `**/*.spec.ts` · `api_clients/` của repo này · `runner/tc_registry` |
| Output | `<stamp>_be_coverage_map.md` — một file, báo cáo đầy đủ |
| Tuỳ chọn | `--check-remote` để `git fetch` trước, cho cảnh báo stale chính xác |
| Thời gian | vài giây |
| Mạng | không cần (`--check-remote` thêm một lần fetch, ~3 giây) |

Map tự mang theo xuất xứ: commit đã đọc, số route trích được, số path client giải được, và
nếu bộ trích bỏ sót gì thì có cảnh báo ở đầu file kèm mục **Extraction losses** ở cuối. Một
route bị bỏ sót sẽ đọc thành *đã cover*, nên những con số đó phải nằm trong báo cáo chứ
không chỉ trên console.

**Cách đọc** — bốn vùng trên 101 route:

| Vùng | Nghĩa |
|---|---|
| `BOTH` | có unit test backend **và** API test của QA |
| `BE ONLY` | chỉ có unit test — DB bị mock, chưa ai chứng minh nó chạy khi ráp thật |
| `QA ONLY` | **chỉ QA đỡ**; skip TC đó là endpoint trống lưới |
| `NEITHER` | **không ai test điểm vào HTTP** |

File map chia `NEITHER` theo mức rủi ro nghiệp vụ, và với mỗi endpoint liệt kê TC nào đang
chạm tới nó.

**Lưu ý** — phép đo ở **tầng controller**. `NEITHER` **không** có nghĩa logic chưa bao giờ
được test; nó nghĩa là không test nào chạm tới điểm vào HTTP, nên guard, DTO validation và
status code đều chưa được kiểm. Phải nói đúng câu đó với BE, không thì họ chỉ vào service
spec và họ đúng.

---

## 2. `python -m utils.be_unit_audit`

**Câu hỏi** — những unit test đó có bảo vệ được gì không?

**Cách hoạt động** — bốn phép dò, tất cả đọc **từ source**. Không tra Bug_Tracker, nên một
API mới ra hôm nay cũng được soi như API cũ.

| Dò | Tìm ra |
|---|---|
| `A` | record không tồn tại nhưng trả `400` thay vì `404` — bắt cả dạng `throw` trực tiếp lẫn dạng `isThrow: true` đi qua helper dùng chung (helper này ném `BadRequestException`) |
| `B` | test có **tên** hứa một quy tắc nghiệp vụ nhưng thân chỉ chứng minh exception đã stub được truyền tiếp. Test có tên nói về *propagation* thì được miễn — chúng làm đúng điều chúng tuyên bố |
| `C` | controller spec **không có** assert lỗi nào: chỉ ghim happy path |
| `D` | guard khai bằng `@UseGuards` mà không spec nào nhắc tới — đường phân quyền chưa được kiểm |

| | |
|---|---|
| Input | chỉ `src/` của backend |
| Output | `<stamp>_be_unit_audit.md` |
| Tuỳ chọn | `--check A` / `B` / `C` / `D` để chạy từng phép dò · `--check-remote` |
| Thời gian | vài giây |

**Lưu ý** — không phát hiện nào **chứng minh** một test là sai. Kết luận đó cần PRD và một
người đọc. Tool chỉ nói nên dành thời gian của người đó vào đâu, và vì sao.

---

## 3. `python -m utils.be_drift`

**Câu hỏi** — backend vừa đổi; tôi phải chạy lại TC nào?

**Cách hoạt động** — diff commit baseline đã ghi với `HEAD` của clone, đi ngược import graph
từ mọi controller (tối đa 3 chặng) để biết file đã đổi ảnh hưởng tới endpoint nào, rồi map
endpoint đó sang TC id. Đồng thời đọc cây file **cũ** bằng `git show` để phát hiện route
trước đây chưa tồn tại.

| | |
|---|---|
| Input | git history của backend · baseline ở `docs/api-snapshots/blazeup/be-commit.txt` |
| Output | `<stamp>_be_drift.md` |
| Tuỳ chọn | `--base <sha>` để diff một ref cụ thể · `--save` để ghi `HEAD` thành baseline mới · `--check-remote` |
| Thời gian | vài giây |

**Cách đọc** — các khối:

* `NEW ENDPOINTS` — mới ship từ sau baseline. `NO TC YET` là một lỗ hổng coverage
* `AFFECTED ENDPOINTS` — kèm TC id đang phủ; `— no TC` nghĩa là BE đổi thứ mà ở đây không
  có gì kiểm
* `WIDE CHANGE` — một module dùng chung đã đổi; chạy cả nhóm thay vì danh sách TC lẻ
* `RE-RUN` — dòng `run_test --execute` copy dán được luôn
* `SHARED LIBRARY BUMPED` — một package `@blazeupai/*` đổi version. Thay đổi hành vi bên
  trong các package đó nằm ở **repo khác** và import graph không thấy được

`--save` không sinh log: nó đánh dấu một commit, không tạo báo cáo.

**Lưu ý** — danh sách TC là **gợi ý**: *"những TC chạm tới endpoint bị ảnh hưởng"*, không
phải *"những TC sẽ đỏ"*. Và baseline là **mốc của riêng mình**, không phải commit staging
đang chạy — service không có endpoint `/version`, còn deploy tag thì nằm ở repo CI dùng chung.

---

## 4. `python -m utils.be_test_blame --run`

**Câu hỏi** — unit test backend này đỏ. Ai đổi cái gì, và họ có cập nhật test không?

**Cách hoạt động** — chạy jest (đúng jest mà `npm test` chạy), rồi với mỗi lỗi lấy ra **một
chuỗi chỉ xuất hiện ở một phía** của diff và lần theo nó qua git:

```
git log -S "<chuỗi>" -- src        commit nào đưa nó vào code
git show --name-only <commit>      commit đó có sửa file spec đang đỏ không
git log -S "<chuỗi>" -- <spec>     spec đó đã BAO GIỜ biết đến nó chưa
```

| | |
|---|---|
| Input | một lần chạy jest · git history của backend |
| Output | `<stamp>_be_test_blame.md` · `be-jest.json` (output thô của jest) |
| Tuỳ chọn | `--json <file>` phân tích một lần chạy đã lưu (**mặc định**, giữ clone read-only)<br>`--run` chạy jest trước (~2 phút)<br>`--run <pattern>` chạy một spec (~10 giây)<br>`--check-remote` fetch trước — kiểm **trước** jest, nên clone cũ tốn 3 giây thay vì 2 phút |
| Thời gian | 2 phút với `--run`, tức thì với `--json` |

Nó in cả khối `Test Suites: / Tests: / Time:`, nên **không cần chạy `npm test` riêng** —
chạy cả hai là thực thi toàn bộ suite hai lần.

**Nó cũng đối chiếu `node_modules` với `package.json` trước khi chạy jest.** `git pull` dịch
source nhưng **không** dịch dependency, nên hai thứ lệch nhau đúng lúc cảnh báo source-cũ nói
mọi thứ đã mới. Đo ngày 2026-09-16: một lần chạy báo **15 suite đỏ**, 14 trong số đó "failed to
run" vì lỗi TypeScript — đọc lên thành "backend hỏng". Nguyên nhân thật là
`@blazeupai/blazeup-global-common` ghim 1.0.275 trong khi `node_modules` giữ 1.0.194 cài từ
năm tuần trước. Sau `npm install`, **cùng commit đó chạy 1073 test và chỉ 1 lỗi thật**. Chỉ so
version **ghim chính xác**; so cả range thì gần như dependency nào cũng kêu, và cảnh báo kêu
suốt là cảnh báo không ai đọc vào ngày nó quan trọng.

Trên Windows dùng `npm install --ignore-scripts`: `postinstall` (`rm -rf`) và `prepare`
(`[ -f ... ]`) của backend này là shell Unix, làm npm chết **sau khi** gói đã cài xong.

**Cách đọc một blame** — dòng kết luận chỉ hiện khi **cả hai** điều kiện đúng cùng lúc:
commit đó **có** cập nhật các spec khác, **và** spec này chưa bao giờ biết đến thay đổi. Tổ
hợp đó chỉ ra test cũ, chứ không phải code sai.

**Lưu ý** — cần một **chuỗi** đặc trưng trong diff. Lỗi toàn số (`expect(count).toBe(3)`),
timeout và lỗi môi trường không cho phép tìm gì cả, khi đó tool in ra bốn lệnh git để bạn tự
truy thay vì đoán bừa. Suite **không chạy được** (lỗi import, file bị lock) được báo đúng
bản chất và **cố ý không** truy commit nào — không có diff thì tên commit là bịa.

---

## Các file trong thư mục này

| Dạng tên | Nội dung |
|---|---|
| `<stamp>_be_coverage_map.md` | báo cáo coverage đầy đủ |
| `<stamp>_be_unit_audit.md` | các phát hiện của audit |
| `<stamp>_be_drift.md` | báo cáo drift |
| `<stamp>_be_test_blame.md` | báo cáo blame |
| `be-jest.json` | output thô của jest cho lần blame gần nhất |

**Một file mỗi lần chạy**, `<stamp>` là `YYYYMMDD-HHMMSS`, nên `ls` đã tự sắp theo thứ tự
chạy. Ba loại còn lại ghi lại **dòng lệnh chính xác**, vì cùng một tool với cờ khác nhau cho
báo cáo khác hẳn; riêng coverage map thì có bảng header thay cho dòng lệnh.

**Toàn bộ thư mục này bị gitignore, trừ hai file README** — chốt 2026-09-16. Mỗi lần chạy sinh
thêm bốn file mới, và file nào cũng tạo lại được bằng cách chạy lại tool, nên chúng là **lịch
sử cục bộ** chứ không phải nội dung của repo. `.gitignore` loại cả thư mục rồi nhận lại hai
README — viết theo chiều đó nên sau này thêm tool mới cũng không phải sửa `.gitignore`.

Hệ quả cần biết: lịch sử này nằm trên **một máy**. Xoá thư mục, hoặc clone mới, là câu hỏi
*"con số đó đổi từ lúc nào"* hết trả lời được. Nếu cần giữ lại một báo cáo cụ thể thì copy nó
ra ngoài — luật ignore chỉ chặn việc commit ngược vào đây.

## Đây là đầu ra, không phải nguồn

Không có gì đọc thư mục này. Xoá nó thì mất lịch sử, không làm hỏng gì.

---

> Bản tiếng Anh: [README.md](README.md). Hai file này **không** có kiểm tra đồng bộ tự động
> (selftest chỉ ràng buộc các cặp `*_TEST_CASES.md`), nên sửa một bên thì sửa cả bên kia.
