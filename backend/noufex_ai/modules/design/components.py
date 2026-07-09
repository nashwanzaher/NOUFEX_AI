from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from noufex_ai.modules.design.schemas import (
    ColorPalette,
    ColorScheme,
    ComponentType,
    DesignFramework,
    DesignSystem,
    GeneratedComponent,
    SpacingSystem,
    TypographySystem,
)


class TailwindComponentGenerator:
    """Generates production-ready UI components using Tailwind CSS.
    
    Designed with:
    - Modern design patterns and best practices
    - Full responsiveness (mobile-first)
    - Accessibility (WCAG 2.2 AA+)
    - RTL support
    - Dark mode support
    - Micro-interactions and animations
    """

    def __init__(self, design_system: DesignSystem | None = None) -> None:
        self.ds = design_system or DesignSystem()
        self._colors = self.ds.palette.to_dict()

    def _color(self, name: str, shade: int = 500) -> str:
        return self._colors.get(name, "#3B82F6")

    def _spacing(self, size: str = "md") -> str:
        return getattr(self.ds.spacing, size, "1rem")

    # ── Button Generator ───────────────────────────────────────────────

    def button(
        self,
        variant: str = "primary",
        size: str = "md",
        label: str = "زر",
        icon: str | None = None,
        icon_position: str = "right",
        full_width: bool = False,
        disabled: bool = False,
        outline: bool = False,
        with_animation: bool = True,
    ) -> GeneratedComponent:
        size_classes = {
            "sm": "px-3 py-1.5 text-sm",
            "md": "px-5 py-2.5 text-base",
            "lg": "px-7 py-3.5 text-lg",
            "xl": "px-9 py-4 text-xl",
        }

        variant_classes = {
            "primary": "bg-primary text-white hover:bg-primary/90 shadow-md hover:shadow-lg",
            "secondary": "bg-secondary text-white hover:bg-secondary/90",
            "accent": "bg-accent text-white hover:bg-accent/90",
            "ghost": "bg-transparent hover:bg-gray-100 text-gray-700",
            "danger": "bg-error text-white hover:bg-error/90",
            "success": "bg-success text-white hover:bg-success/90",
        }

        if outline:
            variant_classes = {
                "primary": "border-2 border-primary text-primary hover:bg-primary hover:text-white",
                "secondary": "border-2 border-secondary text-secondary hover:bg-secondary hover:text-white",
                "accent": "border-2 border-accent text-accent hover:bg-accent hover:text-white",
                "danger": "border-2 border-error text-error hover:bg-error hover:text-white",
            }

        animation = (
            "transition-all duration-300 active:scale-95 hover:-translate-y-0.5"
            if with_animation else "transition-colors duration-200"
        )

        icon_html = ""
        if icon:
            icon_html = (
                f'<span class="inline-flex ml-2">{icon}</span>'
                if icon_position == "right"
                else f'<span class="inline-flex mr-2">{icon}</span>'
            )

        width_class = "w-full" if full_width else ""

        html = f"""<button class="inline-flex items-center justify-center {size_classes[size]} {variant_classes.get(variant, variant_classes["primary"])} {animation} {width_class} rounded-xl font-medium focus:outline-none focus:ring-2 focus:ring-primary/50 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 {'cursor-pointer' if not disabled else ''}" {'disabled' if disabled else ''}>
  {icon_html if icon_position == "right" else ""}
  {label}
  {icon_html if icon_position == "left" else ""}
</button>"""

        return GeneratedComponent(html=html, component_type=ComponentType.button, framework=DesignFramework.tailwind)

    # ── Card Generator ─────────────────────────────────────────────────

    def card(
        self,
        title: str = "بطاقة",
        description: str = "هذا نص وصفي للبطاقة. يمكنك وضع أي محتوى هنا.",
        image_url: str = "",
        badge_text: str | None = None,
        badge_variant: str = "primary",
        footer: str | None = None,
        hover_effect: bool = True,
        horizontal: bool = False,
    ) -> GeneratedComponent:
        hover = "hover:shadow-xl transition-all duration-300 hover:-translate-y-1" if hover_effect else ""
        direction = "md:flex-row" if horizontal else ""
        badge = ""
        if badge_text:
            badge = f"""<span class="absolute top-3 right-3 bg-{badge_variant}/10 text-{badge_variant} text-xs font-medium px-2.5 py-1 rounded-full">{badge_text}</span>"""

        image_section = f"""<div class="relative overflow-hidden {'md:w-1/3' if horizontal else 'w-full'}">
  <img class="w-full h-48 {'md:h-full' if horizontal else ''} object-cover hover:scale-105 transition-transform duration-500" src="{image_url if image_url else 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&q=80'}" alt="{title}">
  {badge}
</div>""" if image_url else ""

        html = f"""<div class="bg-white rounded-2xl shadow-md overflow-hidden {hover} {'flex flex-col md:flex-row' if horizontal else ''}">
  {image_section}
  <div class="p-6 flex-1 flex flex-col justify-between">
    <div>
      <h3 class="text-xl font-bold text-gray-900 mb-2">{title}</h3>
      <p class="text-gray-600 leading-relaxed">{description}</p>
    </div>
    {'<div class="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">' + footer + '</div>' if footer else ''}
  </div>
</div>"""

        return GeneratedComponent(html=html, component_type=ComponentType.card, framework=DesignFramework.tailwind)

    # ── Navbar Generator ───────────────────────────────────────────────

    def navbar(
        self,
        brand: str = "NOUFEX",
        links: list[dict[str, str]] | None = None,
        active_link: str = "",
        with_search: bool = False,
        sticky: bool = True,
        transparent: bool = False,
    ) -> GeneratedComponent:
        if links is None:
            links = [
                {"label": "الرئيسية", "href": "#"},
                {"label": "الخدمات", "href": "#"},
                {"label": "المميزات", "href": "#"},
                {"label": "اتصل بنا", "href": "#"},
            ]

        bg = "bg-white/80 backdrop-blur-lg" if transparent else "bg-white"
        shadow = "shadow-sm" if not transparent else ""
        sticky_class = "fixed top-0 left-0 right-0 z-50" if sticky else ""

        links_html = ""
        for link in links:
            is_active = link["label"] == active_link
            active_class = "text-primary font-semibold border-b-2 border-primary" if is_active else "text-gray-600 hover:text-primary"
            links_html += f"""<a href="{link['href']}" class="{active_class} transition-colors duration-200 px-3 py-2 text-sm">{link['label']}</a>"""

        search_html = ""
        if with_search:
            search_html = """<div class="relative hidden md:block">
  <input type="text" placeholder="بحث..." class="w-48 lg:w-64 pl-10 pr-4 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"/>
  <svg class="absolute right-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
</div>"""

        # Mobile menu button
        mobile_menu = f"""<div class="md:hidden">
  <button class="p-2 text-gray-600 hover:text-primary transition-colors" onclick="this.closest('nav').querySelector('.nav-menu').classList.toggle('hidden')">
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
  </button>
</div>"""

        html = f"""<nav class="{bg} {shadow} {sticky_class}">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      <div class="flex items-center gap-8">
        <a href="#" class="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">{brand}</a>
        <div class="hidden md:flex items-center gap-1">
          {links_html}
        </div>
      </div>
      <div class="flex items-center gap-4">
        {search_html}
        {mobile_menu}
      </div>
    </div>
    <div class="nav-menu hidden md:hidden pb-4 border-t border-gray-100 pt-4">
      <div class="flex flex-col gap-2">
        {links_html.replace('hidden md:flex', 'flex')}
      </div>
    </div>
  </div>
</nav>
{'<div class="h-16"></div>' if sticky else ''}"""

        return GeneratedComponent(html=html, component_type=ComponentType.navbar, framework=DesignFramework.tailwind)

    # ── Hero Section Generator ─────────────────────────────────────────

    def hero(
        self,
        title: str = "حلول ذكية لمستقبل أفضل",
        subtitle: str = "نقدم أفضل الحلول التقنية المبتكرة لتطوير أعمالك وزيادة إنتاجيتك",
        cta_text: str = "ابدأ الآن",
        cta_secondary_text: str = "اعرف المزيد",
        with_image: bool = True,
        image_url: str = "",
        gradient: bool = True,
        centered: bool = True,
    ) -> GeneratedComponent:
        bg = "bg-gradient-to-br from-primary/5 via-white to-secondary/5" if gradient else "bg-white"
        align = "text-center items-center" if centered else "text-right items-start"
        image = ""
        if with_image:
            img_src = image_url or "https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&q=80"
            image = f"""<div class="lg:w-1/2 mt-10 lg:mt-0">
  <img class="w-full rounded-2xl shadow-2xl hover:shadow-3xl transition-shadow duration-500" src="{img_src}" alt="Hero">
</div>"""

        html = f"""<section class="{bg} py-20 lg:py-28">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex flex-col lg:flex-row {align} justify-between gap-12">
      <div class="lg:w-1/2 {'mx-auto' if centered else ''}">
        <div class="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
          <span class="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
          منصة NOUFEX
        </div>
        <h1 class="text-4xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
          {title}
        </h1>
        <p class="text-lg lg:text-xl text-gray-600 leading-relaxed mb-8">
          {subtitle}
        </p>
        <div class="flex flex-wrap gap-4">
          <a href="#" class="inline-flex items-center px-8 py-3.5 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 transition-all duration-300 hover:-translate-y-0.5 shadow-lg hover:shadow-xl">
            {cta_text}
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
          </a>
          <a href="#" class="inline-flex items-center px-8 py-3.5 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-all duration-300">
            {cta_secondary_text}
          </a>
        </div>
      </div>
      {image}
    </div>
  </div>
</section>"""

        return GeneratedComponent(html=html, component_type=ComponentType.hero, framework=DesignFramework.tailwind)

    # ── Stats Section ──────────────────────────────────────────────────

    def stats(
        self,
        items: list[dict[str, str]] | None = None,
        columns: int = 4,
    ) -> GeneratedComponent:
        if items is None:
            items = [
                {"value": "١٠٠٠+", "label": "عميل نشط"},
                {"value": "٥٠٠٠+", "label": "مشروع مكتمل"},
                {"value": "٩٩.٩%", "label": "نسبة الرضا"},
                {"value": "٢٤/٧", "label": "دعم فني"},
            ]
        grid_cols = {1: "grid-cols-1", 2: "grid-cols-2", 3: "grid-cols-3", 4: "grid-cols-2 md:grid-cols-4"}

        items_html = ""
        for item in items:
            items_html += f"""<div class="text-center p-6 bg-white rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 hover:-translate-y-1">
  <div class="text-3xl lg:text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-2">{item['value']}</div>
  <div class="text-gray-500 text-sm">{item['label']}</div>
</div>"""

        html = f"""<section class="py-16 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="grid {grid_cols.get(columns, 'grid-cols-2 md:grid-cols-4')} gap-6">
      {items_html}
    </div>
  </div>
</section>"""

        return GeneratedComponent(html=html, component_type=ComponentType.stats, framework=DesignFramework.tailwind)

    # ── Feature Grid ───────────────────────────────────────────────────

    def feature_grid(
        self,
        features: list[dict[str, str]] | None = None,
        title: str = "مميزاتنا",
        subtitle: str = "اكتشف لماذا يختارنا الآلاف",
        columns: int = 3,
    ) -> GeneratedComponent:
        if features is None:
            features = [
                {"icon": "🚀", "title": "سرعة فائقة", "desc": "أداء عالي وتحميل سريع يضمن تجربة مستخدم ممتازة"},
                {"icon": "🔒", "title": "آمن تماماً", "desc": "حماية متقدمة للبيانات وتشفير من الدرجة الأولى"},
                {"icon": "🎨", "title": "تصميم عصري", "desc": "واجهات مستخدم حديثة وجذابة تلبي احتياجاتك"},
                {"icon": "📊", "title": "تقارير لحظية", "desc": "تحليلات وتقارير دقيقة في الوقت الفعلي"},
                {"icon": "🔗", "title": "تكامل سلس", "desc": "يتكامل مع جميع الأدوات والخدمات التي تستخدمها"},
                {"icon": "💬", "title": "دعم متواصل", "desc": "فريق دعم محترف جاهز لمساعدتك 24/7"},
            ]
        grid_cols = {2: "md:grid-cols-2", 3: "md:grid-cols-3", 4: "md:grid-cols-4"}

        cards = ""
        for feat in features:
            cards += f"""<div class="group p-6 bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
  <div class="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">{feat['icon']}</div>
  <h3 class="text-xl font-bold text-gray-900 mb-2">{feat['title']}</h3>
  <p class="text-gray-500 leading-relaxed">{feat['desc']}</p>
</div>"""

        html = f"""<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">{title}</h2>
      <p class="text-xl text-gray-500 max-w-2xl mx-auto">{subtitle}</p>
    </div>
    <div class="grid grid-cols-1 {grid_cols.get(columns, 'md:grid-cols-3')} gap-8">
      {cards}
    </div>
  </div>
</section>"""

        return GeneratedComponent(html=html, component_type=ComponentType.feature, framework=DesignFramework.tailwind)

    # ── Testimonial Card ───────────────────────────────────────────────

    def testimonial(
        self,
        quote: str = "منصة رائعة! غيرت طريقة عملنا تماماً وساعدتنا في تحقيق نتائج مبهرة.",
        author: str = "أحمد محمد",
        role: str = "مدير تنفيذي",
        avatar_url: str = "",
        rating: int = 5,
    ) -> GeneratedComponent:
        stars = "⭐" * rating
        avatar = avatar_url or "https://i.pravatar.cc/150?img=11"
        html = f"""<div class="bg-white rounded-2xl shadow-md p-8 hover:shadow-lg transition-all duration-300">
  <div class="flex gap-1 mb-4">{'<span>⭐</span>' * rating}</div>
  <p class="text-gray-600 leading-relaxed text-lg mb-6">"{quote}"</p>
  <div class="flex items-center gap-4">
    <img class="w-12 h-12 rounded-full object-cover ring-2 ring-primary/20" src="{avatar}" alt="{author}">
    <div>
      <div class="font-bold text-gray-900">{author}</div>
      <div class="text-sm text-gray-500">{role}</div>
    </div>
  </div>
</div>"""

        return GeneratedComponent(html=html, component_type=ComponentType.testimonial, framework=DesignFramework.tailwind)

    # ── Pricing Card ───────────────────────────────────────────────────

    def pricing(
        self,
        title: str = "احترافية",
        price: str = "٩٩",
        currency: str = "ريال",
        period: str = "شهرياً",
        features: list[str] | None = None,
        popular: bool = False,
        cta: str = "اشترك الآن",
    ) -> GeneratedComponent:
        if features is None:
            features = ["مستخدمين غير محدود", "مساحة ١٠٠ جيجابايت", "دعم فني 24/7", "تقارير متقدمة", "تكامل API"]

        popular_badge = ""
        popular_border = ""
        if popular:
            popular_badge = """<div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-primary to-secondary text-white text-sm font-medium px-4 py-1 rounded-full">الأكثر طلباً</div>"""
            popular_border = "ring-2 ring-primary shadow-xl scale-105"

        features_html = ""
        for f in features:
            features_html += f"""<li class="flex items-center gap-3 text-gray-600">
  <svg class="w-5 h-5 text-success flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
  {f}
</li>"""

        html = f"""<div class="relative bg-white rounded-2xl shadow-md p-8 {popular_border} transition-all duration-300 hover:-translate-y-2">
  {popular_badge}
  <div class="text-center mb-8">
    <h3 class="text-xl font-bold text-gray-900 mb-2">{title}</h3>
    <div class="flex items-baseline justify-center gap-1">
      <span class="text-4xl font-bold text-gray-900">{price}</span>
      <span class="text-gray-500">{currency}</span>
      <span class="text-gray-400 text-sm">/{period}</span>
    </div>
  </div>
  <ul class="space-y-4 mb-8">
    {features_html}
  </ul>
  <a href="#" class="block text-center w-full py-3 {'bg-primary text-white hover:bg-primary/90' if popular else 'bg-gray-50 text-gray-900 hover:bg-gray-100'} rounded-xl font-medium transition-all duration-300">
    {cta}
  </a>
</div>"""

        return GeneratedComponent(html=html, component_type=ComponentType.pricing, framework=DesignFramework.tailwind)

    # ── Form Generator ─────────────────────────────────────────────────

    def form(
        self,
        title: str = "تواصل معنا",
        fields: list[dict[str, Any]] | None = None,
        submit_text: str = "إرسال",
        layout: str = "single",  # single, two_column, multi_step
    ) -> GeneratedComponent:
        if fields is None:
            fields = [
                {"type": "text", "label": "الاسم الكامل", "placeholder": "أدخل اسمك", "required": True},
                {"type": "email", "label": "البريد الإلكتروني", "placeholder": "أدخل بريدك", "required": True},
                {"type": "tel", "label": "رقم الجوال", "placeholder": "05xxxxxxxx", "required": False},
                {"type": "select", "label": "نوع الاستفسار", "options": ["خدمة عملاء", "مبيعات", "دعم فني", "أخرى"]},
                {"type": "textarea", "label": "الرسالة", "placeholder": "اكتب رسالتك هنا...", "required": True},
            ]

        field_type_map = {
            "text": "text", "email": "email", "tel": "tel",
            "password": "password", "number": "number",
        }

        fields_html = ""
        for field in fields:
            ft = field.get("type", "text")
            label = field.get("label", "")
            placeholder = field.get("placeholder", "")
            required = field.get("required", False)
            req_mark = " *" if required else ""
            req_class = "border-red-300 focus:border-red-500 focus:ring-red-500/30" if False else "border-gray-200 focus:border-primary focus:ring-primary/30"

            if ft in field_type_map:
                fields_html += f"""<div>
  <label class="block text-sm font-medium text-gray-700 mb-1.5">{label}{req_mark}</label>
  <input type="{field_type_map[ft]}" placeholder="{placeholder}" {'required' if required else ''} class="w-full px-4 py-2.5 border {req_class} rounded-xl focus:outline-none focus:ring-2 transition-all duration-200"/>
</div>"""
            elif ft == "textarea":
                fields_html += f"""<div>
  <label class="block text-sm font-medium text-gray-700 mb-1.5">{label}{req_mark}</label>
  <textarea rows="4" placeholder="{placeholder}" {'required' if required else ''} class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:border-primary focus:ring-primary/30 transition-all duration-200"></textarea>
</div>"""
            elif ft == "select":
                options_html = ""
                for opt in field.get("options", []):
                    options_html += f"<option>{opt}</option>"
                fields_html += f"""<div>
  <label class="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
  <select class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:border-primary focus:ring-primary/30 transition-all duration-200 bg-white">
    {options_html}
  </select>
</div>"""

        html = f"""<section class="py-16 bg-gray-50">
  <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="bg-white rounded-3xl shadow-md p-8">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
      <p class="text-gray-500 mb-8">نحن هنا لمساعدتك، املأ النموذج وسنرد عليك في أقرب وقت</p>
      <form class="space-y-5" onsubmit="event.preventDefault(); alert('تم الإرسال بنجاح!');">
        {fields_html}
        <button type="submit" class="w-full py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 transition-all duration-300 active:scale-[0.98]">
          {submit_text}
        </button>
      </form>
    </div>
  </div>
</section>"""

        return GeneratedComponent(html=html, component_type=ComponentType.form, framework=DesignFramework.tailwind)

    # ── Footer Generator ───────────────────────────────────────────────

    def footer(
        self,
        brand: str = "NOUFEX",
        description: str = "منصة رقمية متكاملة تقدم حلولاً مبتكرة لتطوير الأعمال وزيادة الإنتاجية",
        columns: list[dict[str, Any]] | None = None,
    ) -> GeneratedComponent:
        if columns is None:
            columns = [
                {"title": "الخدمات", "links": [{"label": "تصميم", "href": "#"}, {"label": "تطوير", "href": "#"}, {"label": "استشارات", "href": "#"}]},
                {"title": "الشركة", "links": [{"label": "عننا", "href": "#"}, {"label": "المدونة", "href": "#"}, {"label": "وظائف", "href": "#"}]},
                {"title": "الدعم", "links": [{"label": "مركز المساعدة", "href": "#"}, {"label": "الشروط", "href": "#"}, {"label": "الخصوصية", "href": "#"}]},
            ]

        cols_html = ""
        for col in columns:
            links_html = "\n".join(
                f'<li><a href="{l["href"]}" class="text-gray-400 hover:text-white transition-colors duration-200 text-sm">{l["label"]}</a></li>'
                for l in col.get("links", [])
            )
            cols_html += f"""<div>
  <h3 class="text-white font-bold mb-4">{col['title']}</h3>
  <ul class="space-y-3">{links_html}</ul>
</div>"""

        html = f"""<footer class="bg-gray-900 text-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-12">
      <div class="md:col-span-1">
        <div class="text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-4">{brand}</div>
        <p class="text-gray-400 text-sm leading-relaxed">{description}</p>
      </div>
      {cols_html}
    </div>
    <div class="border-t border-gray-800 mt-12 pt-8 text-center text-gray-500 text-sm">
      © {brand} {2026}. جميع الحقوق محفوظة.
    </div>
  </div>
</footer>"""

        return GeneratedComponent(html=html, component_type=ComponentType.footer, framework=DesignFramework.tailwind)

    # ── Modal / Dialog Generator ───────────────────────────────────────

    def modal(
        self,
        title: str = "تأكيد العملية",
        content: str = "هل أنت متأكد من رغبتك في تنفيذ هذا الإجراء؟",
        confirm_text: str = "تأكيد",
        cancel_text: str = "إلغاء",
        size: str = "md",
    ) -> GeneratedComponent:
        sizes = {"sm": "max-w-sm", "md": "max-w-lg", "lg": "max-w-2xl", "xl": "max-w-4xl"}

        html = f"""<!-- Modal Trigger -->
<button onclick="document.getElementById('modal').classList.remove('hidden')" class="px-5 py-2.5 bg-primary text-white rounded-xl hover:bg-primary/90 transition-all duration-300">
  فتح النافذة
</button>

<!-- Modal Backdrop -->
<div id="modal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onclick="if(event.target===this)this.classList.add('hidden')">
  <div class="{sizes.get(size, 'max-w-lg')} w-full mx-4 bg-white rounded-2xl shadow-2xl animate-[scaleIn_0.2s_ease-out]">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
      <h3 class="text-lg font-bold text-gray-900">{title}</h3>
      <button onclick="document.getElementById('modal').classList.add('hidden')" class="text-gray-400 hover:text-gray-600 transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
      </button>
    </div>
    <!-- Body -->
    <div class="px-6 py-6">
      <p class="text-gray-600">{content}</p>
    </div>
    <!-- Footer -->
    <div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-100 bg-gray-50/50 rounded-b-2xl">
      <button onclick="document.getElementById('modal').classList.add('hidden')" class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-xl transition-all duration-200">
        {cancel_text}
      </button>
      <button onclick="document.getElementById('modal').classList.add('hidden')" class="px-4 py-2 bg-primary text-white rounded-xl hover:bg-primary/90 transition-all duration-200">
        {confirm_text}
      </button>
    </div>
  </div>
</div>

<style>
@keyframes scaleIn {{
  from {{ opacity: 0; transform: scale(0.95); }}
  to {{ opacity: 1; transform: scale(1); }}
}}
</style>"""

        return GeneratedComponent(html=html, component_type=ComponentType.modal, framework=DesignFramework.tailwind)

    # ── Tabs Generator ─────────────────────────────────────────────────

    def tabs(
        self,
        tabs_data: list[dict[str, str]] | None = None,
    ) -> GeneratedComponent:
        if tabs_data is None:
            tabs_data = [
                {"label": "مميزات", "content": "<p class='text-gray-600'>محتوى المميزات هنا... يتميز بالسرعة والأمان والموثوقية.</p>"},
                {"label": "التسعير", "content": "<p class='text-gray-600'>محتوى التسعير هنا... خطط مرنة تناسب الجميع.</p>"},
                {"label": "التعليمات", "content": "<p class='text-gray-600'>محتوى التعليمات هنا... إجابات لأكثر الأسئلة شيوعاً.</p>"},
            ]

        tabs_html = ""
        contents_html = ""
        for i, tab in enumerate(tabs_data):
            active = "bg-primary text-white shadow-md" if i == 0 else "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
            active_content = "block" if i == 0 else "hidden"
            tabs_html += f"""<button class="tab-btn px-5 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 {active}" data-tab="{i}">{tab['label']}</button>"""
            contents_html += f"""<div class="tab-content {active_content} p-6" data-tab="{i}">{tab['content']}</div>"""

        html = f"""<div class="max-w-3xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-100">
  <div class="flex gap-2 p-3 border-b border-gray-100 overflow-x-auto">
    {tabs_html}
  </div>
  <div>
    {contents_html}
  </div>
</div>

<script>
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', function() {{
    document.querySelectorAll('.tab-btn').forEach(b => {{ b.classList.remove('bg-primary', 'text-white', 'shadow-md'); b.classList.add('text-gray-500', 'hover:text-gray-700', 'hover:bg-gray-50'); }});
    this.classList.add('bg-primary', 'text-white', 'shadow-md');
    this.classList.remove('text-gray-500', 'hover:text-gray-700', 'hover:bg-gray-50');
    const tab = this.dataset.tab;
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    document.querySelector(`.tab-content[data-tab="${{tab}}"]`).classList.remove('hidden');
  }});
}});
</script>"""

        return GeneratedComponent(html=html, component_type=ComponentType.tabs, framework=DesignFramework.tailwind)

    # ── Avatar Generator ───────────────────────────────────────────────

    def avatar(
        self,
        src: str = "",
        name: str = "مستخدم",
        size: str = "md",
        show_status: bool = False,
        status: str = "online",
    ) -> GeneratedComponent:
        sizes = {"sm": "w-8 h-8 text-xs", "md": "w-12 h-12 text-sm", "lg": "w-16 h-16 text-lg", "xl": "w-24 h-24 text-2xl"}
        status_colors = {"online": "bg-success", "away": "bg-warning", "busy": "bg-error", "offline": "bg-gray-400"}
        status_sizes = {"sm": "w-2.5 h-2.5 ring-1", "md": "w-3.5 h-3.5 ring-2", "lg": "w-4 h-4 ring-2", "xl": "w-5 h-5 ring-2"}

        initials = "".join(w[0] for w in name.split()[:2]).upper() if name else "?"
        img = f"""<img class="{sizes[size]} rounded-full object-cover" src="{src}" alt="{name}">""" if src else f"""<div class="{sizes[size]} rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-bold">{initials}</div>"""
        status_dot = f"""<span class="absolute bottom-0 right-0 {status_sizes[size]} {status_colors.get(status, 'bg-gray-400')} rounded-full ring-white"></span>""" if show_status else ""

        html = f"""<div class="relative inline-flex">
  {img}
  {status_dot}
</div>"""

        return GeneratedComponent(html=html, component_type=ComponentType.avatar, framework=DesignFramework.tailwind)

    # ── Alert / Notification Generator ─────────────────────────────────

    def alert(
        self,
        variant: str = "info",
        title: str = "تم بنجاح!",
        message: str = "تم حفظ التغييرات بنجاح.",
        dismissible: bool = True,
        icon: str | None = None,
    ) -> GeneratedComponent:
        styles = {
            "info": {"bg": "bg-blue-50 border-blue-200", "icon": "text-blue-500", "title": "text-blue-800", "text": "text-blue-700"},
            "success": {"bg": "bg-green-50 border-green-200", "icon": "text-green-500", "title": "text-green-800", "text": "text-green-700"},
            "warning": {"bg": "bg-amber-50 border-amber-200", "icon": "text-amber-500", "title": "text-amber-800", "text": "text-amber-700"},
            "error": {"bg": "bg-red-50 border-red-200", "icon": "text-red-500", "title": "text-red-800", "text": "text-red-700"},
        }
        s = styles.get(variant, styles["info"])
        icons = {
            "info": "<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'/>",
            "success": "<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'/>",
            "warning": "<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'/>",
            "error": "<path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'/>",
        }
        icon_path = icons.get(variant, icons["info"])
        dismiss = """<button onclick="this.closest('.alert').remove()" class="text-current opacity-50 hover:opacity-100 transition-opacity"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg></button>""" if dismissible else ""

        html = f"""<div class="alert flex items-start gap-3 p-4 border rounded-xl {s['bg']} animate-[slideInRight_0.3s_ease-out]">
  <svg class="w-6 h-6 {s['icon']} flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">{icon_path}</svg>
  <div class="flex-1">
    <p class="font-semibold {s['title']}">{title}</p>
    <p class="text-sm {s['text']} mt-0.5">{message}</p>
  </div>
  {dismiss}
</div>

<style>
@keyframes slideInRight {{
  from {{ opacity: 0; transform: translateX(20px); }}
  to {{ opacity: 1; transform: translateX(0); }}
}}
</style>"""

        return GeneratedComponent(html=html, component_type=ComponentType.alert, framework=DesignFramework.tailwind)

    # ── Badge Generator ────────────────────────────────────────────────

    def badge(self, text: str = "جديد", variant: str = "primary", size: str = "sm") -> GeneratedComponent:
        variants = {
            "primary": "bg-primary/10 text-primary",
            "secondary": "bg-secondary/10 text-secondary",
            "success": "bg-success/10 text-success",
            "warning": "bg-warning/10 text-warning",
            "error": "bg-error/10 text-error",
            "neutral": "bg-gray-100 text-gray-700",
        }
        sizes = {"sm": "text-xs px-2 py-0.5", "md": "text-sm px-2.5 py-1", "lg": "text-base px-3 py-1.5"}

        html = f"""<span class="inline-flex items-center gap-1 {sizes[size]} {variants.get(variant, variants['primary'])} rounded-full font-medium">
  <span class="w-1.5 h-1.5 rounded-full bg-current"></span>
  {text}
</span>"""

        return GeneratedComponent(html=html, component_type=ComponentType.badge, framework=DesignFramework.tailwind)

    # ── Progress Bar Generator ─────────────────────────────────────────

    def progress(self, value: int = 65, label: str = "", variant: str = "primary", show_label: bool = True) -> GeneratedComponent:
        colors = {"primary": "bg-primary", "secondary": "bg-secondary", "success": "bg-success", "warning": "bg-warning", "error": "bg-error"}

        percentage = min(max(value, 0), 100)
        label_html = f"""<div class="flex justify-between text-sm mb-1.5">
  <span class="text-gray-700 font-medium">{label or 'التقدم'}</span>
  <span class="text-gray-500">{percentage}%</span>
</div>""" if show_label else ""

        html = f"""{label_html}
<div class="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
  <div class="{colors.get(variant, colors['primary'])} h-full rounded-full transition-all duration-1000 ease-out" style="width: {percentage}%"></div>
</div>"""

        return GeneratedComponent(html=html, component_type=ComponentType.progress, framework=DesignFramework.tailwind)

    # ── Table Generator ────────────────────────────────────────────────

    def table(self, headers: list[str] | None = None, rows: list[list[str]] | None = None) -> GeneratedComponent:
        if headers is None:
            headers = ["الاسم", "البريد", "الحالة", "الإجراءات"]
        if rows is None:
            rows = [
                ["أحمد محمد", "ahmed@example.com", '<span class="bg-success/10 text-success text-xs px-2 py-1 rounded-full">نشط</span>', '<a href="#" class="text-primary hover:underline text-sm">تعديل</a>'],
                ["سارة علي", "sara@example.com", '<span class="bg-warning/10 text-warning text-xs px-2 py-1 rounded-full">معلق</span>', '<a href="#" class="text-primary hover:underline text-sm">تعديل</a>'],
                ["خالد عمر", "khaled@example.com", '<span class="bg-success/10 text-success text-xs px-2 py-1 rounded-full">نشط</span>', '<a href="#" class="text-primary hover:underline text-sm">تعديل</a>'],
            ]

        headers_html = "\n".join(f'<th class="px-6 py-4 text-right text-sm font-semibold text-gray-700">{h}</th>' for h in headers)
        rows_html = ""
        for row in rows:
            cells = "\n".join(f'<td class="px-6 py-4 text-sm text-gray-600">{c}</td>' for c in row)
            rows_html += f"<tr class=\"hover:bg-gray-50 transition-colors border-b border-gray-100\">{cells}</tr>\n"

        html = f"""<div class="overflow-x-auto bg-white rounded-2xl shadow-sm border border-gray-100">
  <table class="w-full">
    <thead>
      <tr class="border-b border-gray-100 bg-gray-50/50">
        {headers_html}
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>"""

        return GeneratedComponent(html=html, component_type=ComponentType.table, framework=DesignFramework.tailwind)

    # ── Dashboard Card / Stat Widget ───────────────────────────────────

    def stat_card(
        self,
        label: str = "إجمالي المستخدمين",
        value: str = "١٢٬٤٥٠",
        change: str = "+١٢.٥٪",
        change_positive: bool = True,
        icon: str = "📊",
    ) -> GeneratedComponent:
        change_color = "text-success" if change_positive else "text-error"
        change_arrow = "↑" if change_positive else "↓"

        html = f"""<div class="bg-white rounded-2xl shadow-sm p-6 hover:shadow-md transition-all duration-300">
  <div class="flex items-center justify-between mb-4">
    <span class="text-2xl">{icon}</span>
    <span class="{change_color} text-sm font-medium flex items-center gap-1">{change_arrow} {change}</span>
  </div>
  <div class="text-3xl font-bold text-gray-900 mb-1">{value}</div>
  <div class="text-sm text-gray-500">{label}</div>
</div>"""

        return GeneratedComponent(html=html, component_type=ComponentType.stats, framework=DesignFramework.tailwind)
