# Paper Writing Notes

File này ghi lại quan điểm, phạm vi, và quy tắc văn phong của tôi cho paper trong folder này. Dùng để tự nhắc bản thân và để brief cho người hỗ trợ (Claude, đồng tác giả, reviewer nội bộ) khi bắt đầu session mới.

## 1. Quan điểm nền

Tôi chia malware thành hai phần:

- **Shellcode** — trả lời câu hỏi *what*: malware làm gì? (reverse shell, mã hoá file, self-replicate, exfiltrate, ...). Shellcode là position-independent code, về bản chất có thể thay thế cho nhau.
- **Loader** — trả lời câu hỏi *how*: làm sao qua mặt hệ thống phòng thủ, làm sao đưa shellcode vào, làm sao thực thi được shellcode.

Paper này tập trung hoàn toàn vào **loader**. Shellcode chỉ là biến kiểm soát (controlled variable) để cô lập ảnh hưởng của loader.

## 2. Phạm vi (giữ chặt, không mở rộng)

- **Target OS**: Windows only. Không cross-platform.
- **Security product**: Windows Defender only cho preliminary results. Các AV/EDR khác để future work.
- **Shellcode test**: một payload duy nhất do `msfvenom` sinh (reverse TCP). Không đa dạng payload — vì đây là paper về loader, không phải về shellcode.
- **Loader variants**: tôi tự implement và test được, đủ cho Section 4.

## 3. Contribution status — phải trung thực

### Đã làm (viết thì present tense, "we build", "we evaluate"):
- Pipeline model 6 stage + notation $L_i.T_j$.
- Build platform với compile-time technique selection.
- Các loader variant across L0–L5.
- VM orchestration (KVM/libvirt).
- Telemetry collection skeleton.
- Windows Defender evaluation.

### Chỉ propose (viết thì "we outline", "we propose", + "future work"):
- Stage-aware detection mapping thành rule cụ thể.
- Sigma/YARA rule development.
- Empirical rule verification matrix.
- Multi-product evaluation.
- Real-world loader decomposition case studies.

**Quy tắc vàng**: không viết bảng/ma trận chứa kết quả (rule triggered, detection rate, ...) mà chưa chạy thật. "Paper nêu ý tưởng" ≠ "paper fabricate data". Nếu đã đưa bảng vào thì hoặc chạy thật, hoặc downgrade thành "illustrative example" với ghi chú rõ ràng.

## 4. Văn phong

Tôi là non-native English speaker, muốn prose đơn giản, đủ ý, mạch lạc. Các quy tắc:

1. **Câu ngắn, một ý một câu.** Cắt câu dài có nhiều mệnh đề phụ.
2. **Chủ động > bị động** khi có thể.
3. **Không dùng từ marketing**: "dual-purpose knowledge platform", "systematic" (trừ khi thực sự có ý "có hệ thống"), "comprehensive", "robust", "bridges", "leverages", "facilitates", "encompassing". Thay bằng động từ đơn giản: "builds", "uses", "enables", "covers".
4. **Dùng bold tiết kiệm**. Chỉ bold cho thuật ngữ được định nghĩa lần đầu trong danh sách định nghĩa. Không bold trong đoạn văn thường.
5. **Hạn chế em-dash (`---`)**. Tối đa 1 em-dash / đoạn văn. Ưu tiên dấu chấm phẩy hoặc tách thành 2 câu.
6. **Tránh trạng từ thừa**: "significantly", "particularly", "primarily", "highly", "absolutely" — thường bỏ đi là được.
7. **Không lặp cùng một ý bằng nhiều cách diễn đạt.** Reviewer đọc 1 lần là đủ.

## 5. Formal claims — điều không được viết

- "To our knowledge, no prior work…" — chỉ dùng nếu đã rà soát kỹ, và kèm theo điều kiện ("combines X + Y + Z"). Không khẳng định trần trụi.
- "We validate / We verify" — chỉ khi có số liệu thật. Nếu preliminary, viết "Preliminary experiments indicate".
- "Comprehensive evaluation" — hầu như không bao giờ dùng. N = 18 không phải comprehensive.
- "Revolutionary", "novel" (trừ khi thực sự là lần đầu được đề xuất và có chứng cứ).

## 6. Cấu trúc file

```
docs/paper/
├── main.tex              # preamble + title + abstract + \input các section
├── references.bib        # BibTeX (không dùng thebibliography inline)
├── WRITING_NOTES.md      # file này
└── sections/
    ├── 01_introduction.tex
    ├── 02_related_work.tex    # bao gồm Background (what/how)
    ├── 03_methodology.tex
    ├── 04_experiments.tex
    ├── 05_discussion.tex
    └── 06_conclusion.tex
```

Thứ tự bố cục: Section 2 mở bằng Background (Shellcode/Loader what-how) trước khi review related work, để reader có vocabulary khi đọc phần so sánh.

## 7. Competitor đã nhận diện

Các OSS loader framework cần cite khi nói về related work:

- **Donut** (TheWover) — PE/.NET → PIC shellcode + loader stub.
- **ScareCrow** (Optiv) — EDR bypass, direct syscalls, DLL unhooking.
- **Inceptor** (klezVirus) — template-driven AV/EDR evasion builder.
- **Havoc** (C5pider) — C2 framework with configurable loader module.
- **SysWhispers** (jthuraisamy) — syscall stub generator, thuộc nhóm individual technique.

Khác biệt của paper này so với các framework trên: paper đưa ra **stage-level decomposition cho research**, còn các framework trên là **operator tools** — option surface phẳng, internal opaque, không có controlled experimental harness.

## 8. Compile

- **Overleaf**: upload toàn bộ folder `docs/paper/` → Menu → Settings → Main document = `main.tex`. Default pdfLaTeX + latexmk xử lý BibTeX tự động.
- **Local**: `pdflatex main && bibtex main && pdflatex main && pdflatex main`.
