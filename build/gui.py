from pathlib import Path
from tkinter import (
    Tk, Canvas, Text, Button, PhotoImage, Frame, Label, Scrollbar,
    Radiobutton, IntVar
)

# ---------- ПЪТИЩА КЪМ АСЕТИ ----------
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"D:\Downloads\build\assets\frame0")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


# ---------- ГЛОБАЛНИ СТИЛОВЕ ----------
COLOR_DARK = "#04195F"   # тъмна лента / бутони
COLOR_LIGHT = "#C6D6F8"   # светло-лилав фон (като менюто)
COLOR_TEXT = "#0F172A"

# ---------- HOVER ЕФЕКТ ЗА БУТОНИ ----------


def add_hover_effect(btn):
    """Оцветява бутона в леко сиво и сменя курсора при задържане на мишката."""
    def on_enter(e):
        e.widget.config(
            bg="#d9d9d9", activebackground="#d9d9d9", cursor="hand2")

    def on_leave(e):
        e.widget.config(
            bg=COLOR_DARK, activebackground=COLOR_DARK, cursor="arrow")
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

# ---------- ОБЩ КОНСТРУКТОР ЗА ЕКРАН НА УРОК ----------


def build_lesson_screen(root, title_text, content_text, headings_set, quiz_data, go_back_cb, image_files=None):
    """
    Екран за урок с:
      • ЕДИН общ скрол вдясно (Canvas + Scrollbar), който движи и текста, и снимките
      • Две колони във viewport-а: лява (текст) и дясна (до 2 изображения)
      • Стабилен скрол с колелцето (работи само върху скролируеми уиджети)
      • Превключване 'Въпроси' ⇄ 'Урок'
    Подавай `image_files=["img1.png", "img2.png"]` ако искаш снимки вдясно.
    """

    # Импортираме локално нужните Tkinter класове (за да е самостоятелна функцията)
    from tkinter import Frame, Label, Button, Canvas, Scrollbar, Text, Radiobutton, IntVar, PhotoImage

    # ---- Цветове / стил  ----
    COLOR_DARK, COLOR_LIGHT, COLOR_TEXT = "#04195F", "#C6D6F8", "#0F172A"
    image_files = image_files or []  # ако None → празен списък

    # ---- Мини helper за hover ефект върху бутони (курсор=ръчичка + леко сиво) ----
    def hover(btn, base=COLOR_DARK):
        btn.bind("<Enter>", lambda e: btn.config(
            bg="#d9d9d9", activebackground="#d9d9d9", cursor="hand2"))
        btn.bind("<Leave>", lambda e: btn.config(
            bg=base, activebackground=base, cursor="arrow"))

    # ==== Коренов контейнер на целия екран за урока (ще се .pack()-ва в главния прозорец) ====
    f = Frame(root, bg=COLOR_LIGHT)

    # ============================= ГОРНА ЛЕНТА (назад + заглавие) =============================
    top = Frame(f, bg=COLOR_DARK)
    top.pack(fill="x")

    # Зареждаме иконка „Назад“. Ако липсва файл, показваме текст "Назад".
    try:
        back_img = PhotoImage(file=relative_to_assets("button_back.png"))
    except Exception:
        back_img = None

    back = Button(
        top,
        image=back_img,                      # ако None → няма картинка
        text=("Назад" if back_img is None else ""),  # fallback текст
        compound="left",                    # ако има и текст и иконка → текстът вдясно
        bg=COLOR_DARK, fg="#fff",
        activebackground=COLOR_DARK,
        bd=0, relief="flat",
        command=go_back_cb                  # callback за връщане към началния екран
    )
    back._ref = back_img  # ВАЖНО: пазим референция към картинката, иначе GC я чисти
    back.pack(side="left", padx=12, pady=8)
    hover(back)  # слагаме hover ефекта

    title = Label(top, text=title_text, font=(
        "Inter Black", 20), fg="#fff", bg=COLOR_DARK)
    title.pack(side="left", padx=12, pady=8)

    # =================== ИЗГЛЕД „УРОК“ (Canvas + един Scrollbar) ===================
    # wrapper = контейнер за канваса и скролбара
    wrapper = Frame(f, bg=COLOR_LIGHT)
    wrapper.pack(fill="both", expand=True)

    # Вертикален скролбар вдясно
    vbar = Scrollbar(wrapper, orient="vertical")
    vbar.pack(side="right", fill="y")

    # Канвас, към който вързваме vbar (yscrollcommand)
    cv = Canvas(wrapper, bg=COLOR_LIGHT, bd=0,
                highlightthickness=0, yscrollcommand=vbar.set)
    cv.pack(side="left", fill="both", expand=True)
    vbar.config(command=cv.yview)

    # Вътрешен "viewport" (Frame), в който ще подредим две колони (ляво текст, дясно снимки)
    vp = Frame(cv, bg=COLOR_LIGHT)
    # viewport рамка вътре в канваса
    win_id = cv.create_window((0, 0), window=vp, anchor="nw")

    # Обновяваме scrollregion при промяна на размера/съдържанието във viewport-а
    vp.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    # При resize на канваса → разтягаме viewport-а на цялата видима ширина
    cv.bind("<Configure>", lambda e: cv.itemconfigure(win_id, width=e.width))

    # ---------------- Глобален MouseWheel handler (само за скролируеми уиджети) ----------------
    # Идея: скролваме само уиджети, които имат yscrollcommand („вързан“ скролбар).
    root_win = f.winfo_toplevel()

    def _is_scrollable(w):
        """Връща True, ако widget-ът поддържа yview_scroll И има зададен yscrollcommand."""
        try:
            yc = w.cget("yscrollcommand")
        except Exception:
            yc = None
        return hasattr(w, "yview_scroll") and yc not in (None, "", " ")

    # Вързваме само веднъж за цялото приложение (флагът на root-а пази състоянието)
    if not getattr(root_win, "_wheel_v2", False):
        def _wheel(e):
            # Намираме widget-а под курсора; качваме се към родителите, докато срещнем „скролируем“
            x, y = root_win.winfo_pointerxy()
            w = root_win.winfo_containing(x, y)
            while w is not None and not _is_scrollable(w):
                w = getattr(w, "master", None)
            if not w:
                return

            # Нормализираме посоката:
            #  - Linux праща <Button-4> (up) и <Button-5> (down)
            #  - Win/macOS пращат <MouseWheel> с event.delta (+/-)
            if hasattr(e, "num") and e.num in (4, 5):
                step = -1 if e.num == 4 else 1
            else:
                step = -1 if e.delta > 0 else 1

            try:
                w.yview_scroll(step, "units")
            except Exception:
                pass

        # Глобално слушаме три вида събития (Win/macOS/Linux)
        root_win.bind_all("<MouseWheel>", _wheel)   # Win/macOS
        root_win.bind_all("<Button-4>", _wheel)     # Linux up
        root_win.bind_all("<Button-5>", _wheel)     # Linux down
        root_win._wheel_v2 = True  # маркираме, че вече сме вързали

    # ----------------- Grid: две колони във viewport-а -----------------
    vp.grid_columnconfigure(0, weight=1)  # лявата колона да расте (текст)
    # дясната колона по съдържание (снимки)
    vp.grid_columnconfigure(1, weight=0)

    # ЛЯВА КОЛОНА (текст)
    left = Frame(vp, bg=COLOR_LIGHT)
    left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=16)

    # ДЯСНА КОЛОНА (снимки)
    right = Frame(vp, bg=COLOR_LIGHT)
    right.grid(row=0, column=1, sticky="n", padx=(10, 20), pady=16)

    # ---- Рендер на текста (ред по ред) като Label-и, за да „споделят“ скрол-а на Canvas-а ----
    for raw in content_text.splitlines(True):
        line = raw.rstrip("\n")
        if not line.strip():
            # Празен ред → малък вертикален отстъп
            Label(left, text="", bg=COLOR_LIGHT).pack()
        else:
            # Ако редът е заглавие (съдържа се в headings_set) → bold + underline
            is_hdr = (line.strip() in headings_set)
            Label(
                left,
                text=line,
                font=("Inter", 12, "bold", "underline") if is_hdr else (
                    "Inter", 12),
                bg=COLOR_LIGHT,
                fg=COLOR_TEXT,
                justify="left",
                anchor="w",
                wraplength=900  # ширина за пренасяне на реда
            ).pack(fill="x", anchor="w")

    # Бутон „Въпроси“ под съдържанието (в лявата колона)
    actions = Frame(left, bg=COLOR_LIGHT)
    actions.pack(fill="x", pady=(8, 12))
    btn_q = Button(
        actions,
        text="Въпроси",
        font=("Inter Black", 12),
        bg=COLOR_DARK, fg="#fff",
        bd=0, relief="flat",
        activebackground=COLOR_DARK
    )
    btn_q.pack(anchor="w")
    hover(btn_q)

    # ---- Дясна колона: илюстрации (до 2 PNG); пазим референции, за да не ги чисти GC ----
    if image_files:
        right._refs = []  # ВАЖНО: пазим изображенията тук
        for fname in image_files[:2]:
            try:
                im = PhotoImage(file=relative_to_assets(fname))
                lbl = Label(right, image=im, bg=COLOR_LIGHT, bd=0)
                lbl.pack(pady=6)
                # запазваме `im`, иначе Tk може да не го покаже
                right._refs.append(im)
            except Exception as e:
                print(f"Неуспешно зареждане на {fname}: {e}")

    # =================== ИЗГЛЕД „ВЪПРОСИ“ (Text + Scrollbar) ===================
    # Отделен контейнер, който показваме/скриваме при toggle
    quiz = Frame(f, bg=COLOR_LIGHT)  # скрит по подразбиране

    # Вертикален скрол за въпросите
    sv = Scrollbar(quiz)
    sv.pack(side="right", fill="y")

    # Text поле за въпросите
    qtxt = Text(
        quiz, wrap="word", font=("Inter", 12),
        bg=COLOR_LIGHT, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
        relief="flat", padx=20, pady=16,
        yscrollcommand=sv.set, highlightthickness=0
    )
    qtxt.pack(side="left", fill="both", expand=True)
    sv.config(command=qtxt.yview)

    # Форматиране на заглавието „Мини викторина“
    qtxt.tag_configure("hdr", font=("Inter", 14, "bold"),
                       underline=1, spacing1=6, spacing3=6, foreground=COLOR_DARK)
    qtxt.insert("end", "Мини викторина:\n", ("hdr",))

    # Рендер на въпросите: за всяко Q → Label с текста + група от Radiobutton-и
    vars_ = []
    for i, (q, opts, _c) in enumerate(quiz_data):
        qf = Frame(qtxt, bg=COLOR_LIGHT)
        Label(qf, text=f"{i+1}. {q}", bg=COLOR_LIGHT, fg=COLOR_TEXT,
              font=("Inter", 12, "bold"), anchor="w", justify="left", wraplength=900)\
            .pack(fill="x", pady=(8, 2))
        v = IntVar(value=-1)
        vars_.append(v)
        for idx, opt in enumerate(opts):
            Radiobutton(
                qf, text=opt, variable=v, value=idx,
                bg=COLOR_LIGHT, fg=COLOR_TEXT,
                activebackground=COLOR_LIGHT, selectcolor=COLOR_LIGHT,
                anchor="w", justify="left", wraplength=900
            ).pack(fill="x", padx=12)
        # Вкарваме целия блок (въпрос + опции) вътре в Text чрез window_create
        qtxt.window_create("end", window=qf)
        qtxt.insert("end", "\n")

    # Етикет за резултата от проверката
    res = Label(qtxt, text="", bg=COLOR_LIGHT,
                fg=COLOR_DARK, font=("Inter", 12, "bold"))

    # Функция за проверка на резултата от викторината
    def check():
        score = sum(1 for (_q, _o, correct_idx), v in zip(
            quiz_data, vars_) if v.get() == correct_idx)
        res.config(text=f"Резултат: {score}/{len(quiz_data)}")

    # Долни бутони във „Въпроси“
    actions_q = Frame(qtxt, bg=COLOR_LIGHT)
    btn_back = Button(
        actions_q, text="Назад към урока",
        font=("Inter Black", 12),
        bg=COLOR_DARK, fg="#fff",
        bd=0, relief="flat",
        activebackground=COLOR_DARK
    )
    btn_back.pack(side="left", padx=(0, 10), pady=(6, 12))
    hover(btn_back)

    btn_chk = Button(
        actions_q, text="Провери",
        font=("Inter Black", 12),
        bg=COLOR_DARK, fg="#fff",
        bd=0, relief="flat",
        activebackground=COLOR_DARK,
        command=check
    )
    btn_chk.pack(side="left", pady=(6, 12))
    hover(btn_chk)

    # Вкарваме бутоните и резултата в края на Text-а
    qtxt.window_create("end", window=actions_q)
    qtxt.window_create("end", window=res)
    qtxt.insert("end", "\n")
    qtxt.config(state="disabled")  # заключваме редакцията

    # ============================= Превключване Урок ⇄ Въпроси =============================
    def show_quiz():
        # Скриваме „урок“ и показваме „въпроси“
        wrapper.pack_forget()
        quiz.pack(fill="both", expand=True)
        title.config(text=title_text.split(":")[0] + ": Въпроси")
        qtxt.focus_set()  # даваме фокус на полето с въпросите (по-добър UX)

    def show_lesson():
        # Скриваме „въпроси“ и показваме „урок“
        quiz.pack_forget()
        wrapper.pack(fill="both", expand=True)
        title.config(text=title_text)
        cv.focus_set()    # даваме фокус на канваса (скролът работи веднага)

    # Закачаме командите към бутоните
    btn_q.config(command=show_quiz)
    btn_back.config(command=show_lesson)

    return f


# ---------- ДАННИ ЗА УРОЦИТЕ (текст, секции и въпроси) ----------
LESSON_1_CONTENT = """
Какво е тестване на софтуер?
• Процес за оценка дали продуктът отговаря на изискванията/очакванията и за откриване на дефекти преди продукшън.

Защо е важно?
• Намалява риска и цената от дефекти след пускане.
• Повишава надеждността и доверието в продукта.
• Подпомага решенията (release/no release).

Нива на тестване:
1) Unit – малки части (функции/класове). Бързи, изолирани.
2) Integration – взаимодействие между модули (БД, услуги).
3) System / End-to-End – поведение на цялата система.
4) Acceptance (UAT) – покриване на бизнес изисквания.

Типове тестове:
• Функционални: проверки по спецификация.
• Нефункционални: производителност, сигурност, използваемост.
• Smoke: бързи проверки на критичните пътеки.
• Regression: уверяваме се, че старото поведение не е счупено.
• Sanity: фокусирани проверки след малки промени.

Жизнен цикъл на дефекта:
New → Assigned → In Progress → Fixed → Retest → Verified → Closed (или Reopened)
• Severity (тежест): колко силно влияе на системата.
• Priority (приоритет): колко спешно трябва да се оправи.

Състав на добър тест-кейс:
• ID/Заглавие, Предусловия, Стъпки, Очакван резултат, Данни.
Пример (Login – позитивен):
1) Отвори страницата за вход.
2) Въведи валидни имейл и парола.
3) Натисни „Вход“.
Очаквано: Пренасочване към таблото; вижда се името на потребителя.
"""
LESSON_1_HEADINGS = {
    "Какво е тестване на софтуер?",
    "Защо е важно?",
    "Нива на тестване:",
    "Типове тестове:",
    "Жизнен цикъл на дефекта:",
    "Състав на добър тест-кейс:",
}
LESSON_1_QUIZ = [
    ("Основната цел на тестването е:", [
        "Да ускори разработката на интерфейса",
        "Да замени бизнес анализа",
        "Да оцени покриването на изискванията и да открие дефекти преди продукшън",
        "Да намали броя на разработчиците"
    ], 2),
    ("Правилен ред на нива на тестване (от ниско към високо):", [
        "Integration → Unit → Acceptance → System",
        "Unit → Integration → System/E2E → Acceptance",
        "Acceptance → System/E2E → Integration → Unit",
        "Unit → System/E2E → Integration → Acceptance"
    ], 1),
    ("Smoke тестовете са:", [
        "Пълни регресии върху всички модули",
        "Бързи проверки на критичните пътеки",
        "Само нефункционални тестове",
        "Само тестове на база данни"
    ], 1),
    ("Severity vs Priority означава:", [
        "Severity = спешност, Priority = влияние",
        "Severity = влияние; Priority = спешност за поправка",
        "И двете значат едно и също",
        "Priority е само за дизайнерски дефекти"
    ], 1),
    ("Задължителни елементи на добър тест-кейс са:", [
        "Име на разработчика и версия на ОС",
        "Скриптове за деплой",
        "Предусловия, стъпки и очакван резултат",
        "Диаграма на класовете"
    ], 2),
]

LESSON_2_CONTENT = """
Какво ще научиш:
• Кои техники за проектиране на тестове да ползваш според вида входове и бизнес логика.
• Как да намалиш броя тест-кейсове без да губиш покритие и как да приоритизираш.
• Как да комбинираш техники (EP + BVA, Pairwise + граници) за максимална полза.
• Как да документираш решенията си накратко и проследимо.

Еквивалентно разделяне (Equivalence Partitioning):
• Раздели входовете в валидни/невалидни класове; избери представител(и) от всеки клас.
• Намалява прегледа от „всички стойности“ до „смислени представители“.
• Включи класове като празна стойност, NULL, специални символи/локали (ако е текст).
• Пример „възраст“ 18–65: класове <18, 18–65 (валидни), >65; тествай по 1–2 представители.

Гранични стойности (Boundary Value Analysis):
• Тестваме min−1, min, min+1 и max−1, max, max+1 (off-by-one грешки са чести).
• Уточни дали границите са включени/изключени; отрази го в тестовете.
• Освен числа — прилагай и за дължини на полета, дати/часове, суми по кошница.
• Комбинирай с EP: покрий границите във всеки валиден/невалиден клас.

Таблици на решенията (Decision Tables):
• Полезни при много правила/условия → изгради матрица Условия × Действия.
• Покрий уникални комбинации; обедини редове с еднакъв изход (където е коректно).
• Добави ред „по подразбиране/else“, за да валидираш липсващи правила.
• Пример: отстъпки по клиентски сегмент × метод на плащане × сезон (валидна/невалидна комбинация).

Преходи на състояния (State Transition Testing):
• Идентифицирай състояния, събития и позволени/забранени преходи.
• Тествай невалидни събития в дадено състояние (очаквана грешка/игнориране).
• Покрий и броячи/таймаути (напр. заключване след N опита, автоматично отключване след T мин).
• Пример: Login → (3 грешни опита) → Locked → (изтича време/админ отключва) → Active.

Комбинаторно (Pairwise/All-pairs):
• Pairwise (t=2) гарантира, че всяка двойка стойности се среща поне веднъж → малко тестове, добро покритие.
• Дефинирай ограничения (constraints), за да изключиш невъзможни комбинации.
• „Seed“-ни критични сценарии ръчно, после допълни с pairwise генератор.
• При нужда повиши силата до t=3 за чувствителни зони (повече покритие, повече тестове).

Изследователско тестване (Exploratory):
• Определи „чартър“ (цел), timebox (30–60 мин) и рискове/хипотези за атака.
• Води кратки бележки: какво пробва, какво очакваше/наблюдава, дефекти/подозрения.
• Ползвай „турове“ (data tour, interface tour, error tour) за систематично покритие.
• Завърши с кратък дебриф: открития, следващи стъпки, идеи за автоматизация.

Практически съвети:
• Комбинирай техники: EP за класове, BVA за точките в/край класовете, Pairwise за параметри.
• Стартирай от най-рисковите/критични потоци; автоматизирай стабилните сценарии.
• Поддържай тестовете кратки, независими и проследими (ID → изискване/правило).
"""
LESSON_2_HEADINGS = {
    "Какво ще научиш:",
    "Еквивалентно разделяне (Equivalence Partitioning):",
    "Гранични стойности (Boundary Value Analysis):",
    "Таблици на решенията (Decision Tables):",
    "Преходи на състояния (State Transition Testing):",
    "Комбинаторно (Pairwise/All-pairs):",
    "Изследователско тестване (Exploratory):",
    "Практически съвети:",
}
LESSON_2_QUIZ = [
    ("Еквивалентно разделяне означава:", [
        "Да тестваш всички възможни стойности",
        "Да избереш по един представител от всеки клас",
        "Само граничните стойности",
        "Случайни стойности"
    ], 1),
    ("Кои са добри гранични тестове за валиден диапазон 18–65 (вкл.)?", [
        "18 и 65",
        "17, 18, 19 и 64, 65, 66",
        "16 и 66",
        "Само 18 и 65 по веднъж"
    ], 1),
    ("Кога използваме таблици на решенията?", [
        "Когато има много комбинации от условия и действия",
        "Когато има само едно поле с число",
        "Когато няма бизнес правила",
        "Когато избираме цветове на UI"
    ], 0),
    ("Фокус при тестване на преходи на състояния:", [
        "Разрешени и забранени преходи между състояния",
        "Само цветове и подредба на екрана",
        "Типове данни и сериализация",
        "SQL оптимизация"
    ], 0),
    ("Основно предимство на pairwise:", [
        "Тества всички комбинации от стойности",
        "С малко тестове покрива всички двойки стойности",
        "Използва се само за сигурност",
        "Подходящо е само за производителност"
    ], 1),
]

LESSON_3_CONTENT = """
Какво ще научиш:
• Как се правят тестова стратегия и тестов план (scope, подход, рискове).
• Как се осигуряват среди/данни и как се планира капацитет.
• Как се докладват дефекти и какви метрики следим.

Тестова стратегия vs. тестов план:
• Стратегия = high-level насоки (какво, защо, подходи, рискове, инструменти).
• План = конкретика за релийз/проект (обхват, екип, график, вход/изход критерии).
• Включи рискове и предположения; дефинирай out of scope.
• Определи критерии за готовност (Entry) и приемане (Exit/Done).

Матрица за проследяване на изискванията (RTM):
• Свързва изисквания → тест-кейсове → дефекти → статути (проследимост).
• Помага да видиш непокрити изисквания или „сиротни“ тестове.
• Ползвай уникални ID-та и линкове към артефакти/тикети.
• Обновявай след всяка промяна на изискванията.

Оценка на усилие и график:
• Оцени по сложност/обем, риск и автоматизируемост.
• Планирай buffer за регресии и фиксове; синхронизирай с релийз влакове.
• Разпределяй по умения (API/UI/мобилно/данни), предвиди code freeze.
• Воденето на burn-down/percent complete помага за статуса.

Метрики и докладване:
• Покритие (by req/код), pass/fail, дефекти по тежест/приоритет.
• Defect leakage/escape (колко са минали към по-късен етап/продукшън).
• Mean Time to Detect/Fix, фуния на дефектите по етапи.
• Кратък репорт: какво тествахме, какво не, рискове, препоръка за релийз.

Дефект репорт (Bug Report):
• Полета: Заглавие, Описание, Стъпки, Очаквано/Реално, Среда/версия, Приложения.
• Severity (влияние) и Priority (спешност) – подбирай обективно.
• Възпроизводимост и минимални стъпки → по-бърз фикс.
• Добави логове/скрийншотове; свържи към тест-кейс/изискване.

Добри практики:
• Кратки и ясни тестове; независими, повтаряеми, с реалистични данни.
• Избягвай „flake“ – стабилизирай среди/данни, reset след тест.
• Автоматизирай критични регресии; ръчни проверки за UX/edge случаи.
• Седмичен sync с екипа: статус, блокери, рискове, следващи стъпки.
"""
LESSON_3_HEADINGS = {
    "Какво ще научиш:",
    "Тестова стратегия vs. тестов план:",
    "Матрица за проследяване на изискванията (RTM):",
    "Оценка на усилие и график:",
    "Метрики и докладване:",
    "Дефект репорт (Bug Report):",
    "Добри практики:",
}
LESSON_3_QUIZ = [
    ("Разлика между стратегия и план е най-добре описана като:", [
        "Стратегия = конкретни дати; План = общи насоки",
        "Стратегия = общи насоки и подход; План = конкретика за релийз/проект",
        "Няма разлика, синоними са",
        "Стратегия е само за автоматизация"
    ], 1),
    ("Кое НЕ е типично поле в добър дефект репорт?", [
        "Очакван резултат", "Реален резултат", "Любим цвят на тестера", "Стъпки за възпроизвеждане"
    ], 2),
    ("RTM служи, за да:", [
        "Оптимизира скоростта на база данни", "Измерва само производителност",
        "Управлява CI/CD пайплайна", "Проследява покритието на изисквания от тестове и дефекти"
    ], 3),
    ("Кои три метрики са полезни в статуса на тестване?", [
        "Брой тестери, брой джира филтри, любим IDE",
        "Pass/Fail, дефекти по тежест, defect leakage",
        "Само брой тест-кейсове", "Само време за билд"
    ], 1),
    ("Severity и Priority означават:", [
        "Severity = влияние върху системата; Priority = спешност за поправка",
        "Severity = спешност; Priority = влияние", "Едно и също", "Priority само за production дефекти"
    ], 0),
]

LESSON_4_CONTENT = """
Какво ще научиш:
• Как работят HTTP/REST и какво тестваме при API.
• Разлика между методи, статуси, заглавия, тяло и как влияят на тестовете.
• Идемпотентност/безопасност, позитивни/негативни сценарии, устойчивост.
• Пагинация/сортиране/филтри, контракт (OpenAPI/JSON Schema), основи на сигурността.

HTTP основи:
• Ресурси (URI), методи: GET/POST/PUT/PATCH/DELETE, заглавия (Content-Type, Accept, Authorization).
• Тяло обикновено JSON; кодиране/локал; дата/час формати (ISO 8601), номера/десетични.
• Идентификатори в path vs. query (resource/{id} vs ?filter=…).

Статус кодове:
• 2xx успех (200 OK, 201 Created, 204 No Content).
• 4xx клиентска грешка (400, 401, 403, 404, 409, 422, 429).
• 5xx сървърна грешка (500, 503) – не издавай вътрешни подробности.
• Консистентна структура на грешка: { code, message, details? }.

Идемпотентност и безопасност:
• Safe: GET/HEAD/OPTIONS не променят състояние.
• Idempotent: GET/PUT/DELETE/HEAD/OPTIONS (POST/ PATCH не са по дефиниция).
• Повторения/timeout-и → Idempotency-Key за POST, exponential backoff.

Дизайн на тестове:
• Позитивни + негативни сценарии (липсващи/грешни полета, типове, граници, невалиден JSON).
• Проверявай заглавия (Content-Type, кеш), кодировка, големи payload-и, специални символи.
• Конкурентност/повторения: дублиран POST, паралелни PUT/DELETE.

Контракт/схема:
• Валидирай срещу OpenAPI/JSON Schema (типове, required, enum, patterns).
• Внимавай за компатибилност при версии; schema drift = счупени клиенти.

Пагинация, филтър, сортиране:
• offset/limit или cursor; max limit и дефолт.
• Стабилно сортиране → без дубли/липси между страници; next/prev линкове.
• Валидирай гранични стойности (page=0, limit<0, огромен limit).

Грешки и устойчивост:
• Таймаути, 5xx, мрежови грешки → коректни таймаути и ретраи.
• Разлика 422 (валидация) vs 409 (конфликт) vs 400 (лошо искане).

Сигурност (основи):
• Auth vs Authz, токени/scope/изтичане; не изтичай чувствителни данни в грешки.
• Rate limit, защита от груба сила; CORS (ако е публичен API).

Практика:
• Инструменти: curl/Postman/HTTPie; среди/колекции/променливи.
• Автоматизация: smoke за критични крайни точки; schema validation в CI.
"""
LESSON_4_HEADINGS = {
    "Какво ще научиш:", "HTTP основи:", "Статус кодове:", "Идемпотентност и безопасност:",
    "Дизайн на тестове:", "Контракт/схема:", "Пагинация, филтър, сортиране:",
    "Грешки и устойчивост:", "Сигурност (основи):", "Практика:",
}
LESSON_4_QUIZ = [
    ("Кой метод НЕ е идемпотентен по дефиниция?",
     ["GET", "PUT", "POST", "DELETE"], 2),
    ("Кога е подходящо да върнем 201 Created?", [
        "При успешно създаване на ресурс чрез POST", "При успешен GET на списък",
        "Когато потребителят няма права", "При вътрешна грешка на сървъра"
    ], 0),
    ("Кое е добър пример за негативен тест?", [
        "Валиден токен и очакван 200", "Невалидна схема/тип на поле → 422",
        "GET на съществуващ ресурс → 200", "POST с валидни данни → 201"
    ], 1),
    ("Кое твърдение за пагинация е вярно?", [
        "Не е нужно да валидираме limit",
        "Трябва стабилно сортиране, за да няма дубли/липси между страници",
        "page=0 винаги е валиден", "next/prev линкове са излишни"
    ], 1),
    ("Как да избегнем дублирано създаване при повторен POST?", [
        "Idempotency-Key + backoff", "Да повторим заявката без промени",
        "Да изтрием ресурса след всяка заявка", "Да използваме само GET"
    ], 0),
]

LESSON_5_CONTENT = """
Какво ще научиш:
• Как да избираш стабилни локатори и да намалиш „flake“ тестовете.
• Кога да използваш явни изчаквания и как да синхронизираш стъпките.
• Как да структурираш UI тестове (Page Object/Screenplay) и да поддържаш код.
• Основи на визуални проверки, крос-браузър/резолюции и достъпност (a11y).

Локатори:
• Предпочитай стабилни атрибути (data-test-id/role/name) пред крехки XPath-ове.
• Избягвай :nth-child/абсолютен XPath по индекс; чупят се при малки промени.
• Използвай ARIA role/name/label за по-устойчиви селектори и по-добра достъпност.
• Централизирай селекторите (Page Object) – лесна подмяна при промяна на UI.

Синхронизация и стабилност:
• Явни изчаквания за условие (елемент видим/кликаем, мрежа тиха) > фиксиран sleep.
• Минимизирай implicit wait; комбинирай retry/backoff за нестабилни действия.
• Изолирай тестовете: чисти cookies/storage, reset състояние, фиксирай test data.
• Стартирай в „headless“ и „headed“ режими при нужда; логвай снимки/видео при грешка.

Архитектура на тестовете (POM/Screenplay):
• Page Object: методи за действия + селектори на едно място → по-малко дублиране.
• Screenplay: актьори/задачи/въпроси → добра композиция за сложни сценарии.
• DRY: helper-и за често срещани стъпки (login, навигация, запълване на форми).
• Поддържай ясни данни/фикстури; избягвай зависимости между тестовете.

Визуални проверки:
• Snapshot/visual diff за ключови екрани; контролирай динамични региони (mask).
• Тествай различни теми/локали/OS шрифтове; настрой прагове за толеранс.
• Комбинирай визуални с функционални проверки (не разчитай само на снимка).

Крос-браузър/резолюции:
• Смеси от браузъри и размери (desktop/tablet/mobile breakpoints).
• Стабилно сортиране на тестовете и паралелизация; ограничение на брой успоредни сесии.
• Фокус върху критични сценарии; не дублирай без нужда същите тестове навсякъде.

Достъпност (a11y):
• Проверявай role/name/label и tab навигация; контраст и фокус-видимост.
• Alt/aria-label за значими елементи; без keyboard trap.
• Интегрирай бърз a11y линтер/плъгин в CI и smoke.

Най-чести проблеми и решения:
• Flaky кликове → по-добри локатори + explicit wait + scroll-into-view.
• Бавни тестове → споделени фикстури, по-малко E2E, повече component/contract.
• Нестабилни среди → mock/stub за външни услуги, seed-нати данни, идемпотентни бекове.

Практика:
• Инструменти: Playwright/Cypress/Webdriver; репорти + скрийншоти в CI.
• UI пирамида: малко E2E, повече компонентни/интеграционни → по-бързи обратни връзки.
"""
LESSON_5_HEADINGS = {
    "Какво ще научиш:",
    "Локатори:",
    "Синхронизация и стабилност:",
    "Архитектура на тестовете (POM/Screenplay):",
    "Визуални проверки:",
    "Крос-браузър/резолюции:",
    "Достъпност (a11y):",
    "Най-чести проблеми и решения:",
    "Практика:",
}
LESSON_5_QUIZ = [
    ("Кой локатор е най-стабилен за UI тест?", [
        "Абсолютен XPath по индекс", "data-test-id / role+name",
        "CSS :nth-child селектор", "Търсене по видим текст без role"
    ], 1),
    ("Кое е вярно за синхронизацията?", [
        "Фиксиран sleep е за предпочитане", "Implicit wait решава всички проблеми",
        "Explicit wait за конкретно условие е за предпочитане", "Не е нужна"
    ], 2),
    ("Основно предимство на Page Object е:", [
        "Кодът става по-дълъг", "Селектори и действия са капсулирани и преизползваеми",
        "Тестване без браузър", "Премахва нуждата от изчаквания"
    ], 1),
    ("Визуалните тестове са полезни за:", [
        "Производителност", "UI регресии (snapshot/diff)", "Валидиране на API", "Покритие на код"
    ], 1),
    ("Кое намалява flakiness най-много?", [
        "Паралелни кликове без изчакване",
        "Стабилни локатори + explicit waits + reset на състоянието",
        "Зависимости между тестовете", "Случайни паузи"
    ], 1),
]

LESSON_6_CONTENT = """
Какво ще научиш:
• Основни понятия: латентност, пропускателност (throughput), едновременност (concurrency), опашка.
• Как се проектира товар: ramp-up/steady/soak/spike/stress и кога се използват.
• Кои метрики следим (p95/p99, грешки, наситеност на ресурси) и как определяме SLA/SLO.
• Как да четем резултати и да намираме тесни места (база данни, мрежа, код).

Основни понятия и цели:
• Латентност = време за отговор; throughput = заявки/сек; concurrency = активни едновременни потребители/заявки.
• Цели/критерии: напр. p95 < 300 ms, грешки < 1%, CPU/Memory/IO < 80% в steady state.
• Опашки/бекпрешър: при наситеност расте опашка → латентност скача → контролирай с лимити и graceful отказ.

Проектиране на товар:
• Ramp-up: постепенно повишаване до целевия товар; избягва фалшиви пикове.
• Steady/state: стабилен сегмент за измерване; Soak (дълъг) за течове/устойчивост.
• Spike/Stress: внезапни скокове/над целта за устойчивост и лимити.
• Модел: потребители vs RPS; мисли за „think time“, реалистично разпределение и корелация.

Метрики и наблюдение:
• Персентили p95/p99 са по-показателни за „опашката“ от средното/медиана.
• Грешки по тип (4xx/5xx/timeout); saturation: CPU, памет, дисков/мрежов IO, connection pools.
• Вътрешни тайминги: DNS/TLS/време за заявка към БД/кеш; логове с корелационни ID.
• Внимавай за „coordinated omission“ – клиентът да не маскира латентности при блокиране.

Сценарии за изпитване:
• Позитивни/негативни; реални данни/разпределения; payload размери.
• Пагинация/филтри/сортиране; качване/сваляне на файлове; burst-и.
• Ретраи/бекоф; лимити/котви (rate limit, circuit breaker) и очаквано поведение.

Среди и данни:
• Среда, близка до продукшън (конфигурации, размери); затопляне (warm-up) и кеши.
• Стабилни тестови данни и изолация; seed/cleanup; фиксирани версии на зависимости.
• Контрол на вариацията: повтаряемост, същия build, същите параметри.

Диагностика и типични тесни места:
• БД: липсващи индекси, N+1, бавни заявки, блокировки/дедлоки.
• Мрежа: TLS handshakes, връзки, MTU/packet loss, head-of-line blocking.
• Приложение: GC паузи, синхронизации/локове, сериен код на горещ път.
• Кешове/CDN: нисък hit ratio, неправилно инвалидиране.

Добри практики:
• Определи вход/изход критерии; дефинирай стоп условия (SLA нарушено, грешки↑).
• Сравнявай спрямо baseline; събирай артефакти (графики, лога, конфиги).
• Малко E2E под голям товар; повече компонент/contract тестове за локализиране.
• Автоматизирай smoke performance в CI; периодични soak/stress извън пикови часове.

Практика:
• Инструменти: k6/JMeter/Gatling/Locust; репорти и експорти към Grafana/Influx/Prometheus.
• Скриптове с параметри (данни, RPS, продължителност); шаблон за доклад и шаблон за сравнение на рунове.
"""
LESSON_6_HEADINGS = {
    "Какво ще научиш:", "Основни понятия и цели:", "Проектиране на товар:",
    "Метрики и наблюдение:", "Сценарии за изпитване:", "Среди и данни:",
    "Диагностика и типични тесни места:", "Добри практики:", "Практика:",
}
LESSON_6_QUIZ = [
    ("Кой показател е най-полезен за „опашката“ на латентността?", [
        "Средно време (avg)", "Медиана (p50)", "Персентили p95/p99", "Минимално време"
    ], 2),
    ("Кое описва правилно ramp-up при натоварване?", [
        "Започваме веднага с максимален товар", "Постепенно увеличаваме до целевия товар",
        "Поддържаме постоянен товар без промяна", "Намаляваме товара към края"
    ], 1),
    ("Кое твърдение е вярно за throughput и concurrency?", [
        "Throughput = едновременни потребители", "Concurrency = заявки/сек",
        "Throughput = заявки/сек, Concurrency = едновременни активни", "Едно и също са"
    ], 2),
    ("Кое е смислено стоп условие за теста?", [
        "Когато дизайнерът одобри цветовете",
        "p95 под целта, грешки < 1%, ресурси < 80% устойчиво",
        "CPU удари 100% за 1 секунда", "Има поне 10 заявки в лога"
    ], 1),
    ("Кое е типично тясно място?", [
        "Липсващи индекси/бавни заявки в БД", "Използване на CDN",
        "Логване на грешки", "Събиране на метрики"
    ], 0),
]

# Събираме всичко в един речник: lesson_no -> (title, content, headings, quiz, снимки (optional) )
lessons_data = {
    1: ("Урок 1: Въведение в тестването на софтуер", LESSON_1_CONTENT, LESSON_1_HEADINGS, LESSON_1_QUIZ, ["lesson1_1.png"]),
    2: ("Урок 2: Техники за проектиране на тестове", LESSON_2_CONTENT, LESSON_2_HEADINGS, LESSON_2_QUIZ, ["lesson2_1.png", "lesson2_2.png"]),
    3: ("Урок 3: Планиране на тестове и управление на дефекти", LESSON_3_CONTENT, LESSON_3_HEADINGS, LESSON_3_QUIZ, ["lesson3_1.png", "lesson3_2.png"]),
    4: ("Урок 4: API тестване – основи", LESSON_4_CONTENT, LESSON_4_HEADINGS, LESSON_4_QUIZ, ["lesson4_1.png", "lesson4_2.png"]),
    5: ("Урок 5: Тестване на UI – локатори, стабилност и синхронизация", LESSON_5_CONTENT, LESSON_5_HEADINGS, LESSON_5_QUIZ, ["lesson5_1.png", "lesson5_2.png"]),
    6: ("Урок 6: Натоварване и производителност – основи", LESSON_6_CONTENT, LESSON_6_HEADINGS, LESSON_6_QUIZ, ["lesson6_1.png", "lesson6_2.png"]),
}

# ---------- ОСНОВЕН ПРОЗОРЕЦ ----------
window = Tk()
window.geometry("1440x1024")
window.configure(bg=COLOR_DARK)
window.title("QA APP TUGAB")
icon = PhotoImage(file=relative_to_assets("iconlogo.png"))
window.iconphoto(True, icon)


# Зареждаме общата картинка за back бутона (един път)
BACK_IMG = PhotoImage(file=relative_to_assets("button_back.png"))

# ---------- HOME ЕКРАН ----------
canvas = Canvas(
    window, bg=COLOR_DARK, height=1024, width=1440,
    bd=0, highlightthickness=0, relief="ridge"
)
canvas.place(x=0, y=0)

# Фонова светло-лилава зона долу
canvas.create_rectangle(0.0, 228.0, 1440.0, 1024.0,
                        fill=COLOR_LIGHT, outline="")

# Логотипи/изображения горе (държим референции към PhotoImage!)
image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
canvas.create_image(1333.0, 117.0, image=image_image_1)

image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
canvas.create_image(123.0, 107.0, image=image_image_2)

canvas.create_text(
    295.0, 50.0, anchor="nw",
    text="Обучение за тестване на качеството\n                       на софтуер",
    fill="#FFFFFF", font=("Inter Black", 48 * -1)
)

# Бутони 1–6 (с изображения) на началния екран
button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
button_1 = Button(image=button_image_1, borderwidth=0, highlightthickness=0,
                  relief="flat", bg=COLOR_DARK, activebackground=COLOR_DARK)
button_1.place(x=10.0, y=410.0, width=440.0, height=146.0)

button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
button_2 = Button(image=button_image_2, borderwidth=0, highlightthickness=0,
                  relief="flat", bg=COLOR_DARK, activebackground=COLOR_DARK)
button_2.place(x=500.0, y=410.0, width=440.0, height=146.0)

button_image_3 = PhotoImage(file=relative_to_assets("button_3.png"))
button_3 = Button(image=button_image_3, borderwidth=0, highlightthickness=0,
                  relief="flat", bg=COLOR_DARK, activebackground=COLOR_DARK)
button_3.place(x=990.0, y=410.0, width=440.0, height=146.0)

button_image_4 = PhotoImage(file=relative_to_assets("button_4.png"))
button_4 = Button(image=button_image_4, borderwidth=0, highlightthickness=0,
                  relief="flat", bg=COLOR_DARK, activebackground=COLOR_DARK)
button_4.place(x=10.0, y=698.0, width=440.0, height=146.0)

button_image_5 = PhotoImage(file=relative_to_assets("button_5.png"))
button_5 = Button(image=button_image_5, borderwidth=0, highlightthickness=0,
                  relief="flat", bg=COLOR_DARK, activebackground=COLOR_DARK)
button_5.place(x=500.0, y=698.0, width=440.0, height=146.0)

button_image_6 = PhotoImage(file=relative_to_assets("button_6.png"))
button_6 = Button(image=button_image_6, borderwidth=0, highlightthickness=0,
                  relief="flat", bg=COLOR_DARK, activebackground=COLOR_DARK)
button_6.place(x=990.0, y=698.0, width=440.0, height=146.0)

# Добавяме hover за всички home бутони
for b in (button_1, button_2, button_3, button_4, button_5, button_6):
    add_hover_effect(b)

# ---------- НАВИГАЦИЯ МЕЖДУ ЕКРАНИ ----------
lesson_frames = {}  # lesson_no -> Frame


def hide_all_lessons():
    """Скрива всички създадени lesson frame-ове и показва началния екран."""
    for fr in lesson_frames.values():
        if fr and fr.winfo_ismapped():
            fr.pack_forget()
    canvas.place(x=0, y=0)


def open_lesson(n: int):
    """Показва урок n. Създава го при първо отваряне, после само го показва."""
    # Скриваме началния екран и всички други уроци
    canvas.place_forget()
    for fr in lesson_frames.values():
        if fr and fr.winfo_ismapped():
            fr.pack_forget()

    if n not in lessons_data:
        return  # няма такъв урок

    entry = lessons_data[n]
    title, content, headings, quiz = entry[:4]
    images = entry[4] if len(entry) > 4 else []  # опционално
    if n not in lesson_frames:
        lesson_frames[n] = build_lesson_screen(
            window, title, content, headings, quiz,
            go_back_cb=hide_all_lessons,
            image_files=images
        )
    lesson_frames[n].pack(fill="both", expand=True)


# Закачаме командите на бутоните 1..6
buttons = {1: button_1, 2: button_2, 3: button_3,
           4: button_4, 5: button_5, 6: button_6}
for i in range(1, 7):
    buttons[i].configure(command=lambda i=i: open_lesson(i))

window.resizable(False, False)
window.mainloop()
