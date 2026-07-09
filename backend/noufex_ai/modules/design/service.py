from __future__ import annotations

import json
from typing import Any

from noufex_ai.modules.design.animations import AnimationEngine
from noufex_ai.modules.design.components import TailwindComponentGenerator
from noufex_ai.modules.design.reviewer import UIReviewEngine
from noufex_ai.modules.design.schemas import (
    ColorPalette,
    ColorScheme,
    ComponentType,
    DesignFramework,
    DesignSystem,
    DesignReviewResult,
    GeneratedComponent,
    TypographySystem,
)
from noufex_ai.settings import settings


class DesignService:
    """Professional UI/UX Design Service.
    
    Capabilities competitive with Kimi K2.7 Code:
    - Component generation (50+ components)
    - Full page generation
    - Design system creation
    - UI review & critique
    - Animation generation
    - Accessibility checking
    - Color theory & typography
    - Responsive design
    """

    def __init__(self) -> None:
        self._reviewer = UIReviewEngine()
        self._animations = AnimationEngine()
        self._current_ds: DesignSystem = DesignSystem(
            name="NOUFEX Design System",
            palette=ColorPalette.from_primary(
                settings.design_default_primary_color,
                ColorScheme(settings.design_default_scheme),
            ),
            typography=TypographySystem(font_family=settings.design_default_font_family),
        )
        self._generator = TailwindComponentGenerator(self._current_ds)

    # ── Design System Management ───────────────────────────────────────

    def create_design_system(
        self,
        name: str = "NOUFEX Design System",
        primary_color: str = "#3B82F6",
        scheme: ColorScheme = ColorScheme.light,
        font_family: str = "Inter, system-ui, sans-serif",
    ) -> DesignSystem:
        palette = ColorPalette.from_primary(primary_color, scheme)
        self._current_ds = DesignSystem(
            name=name,
            palette=palette,
            typography=TypographySystem(font_family=font_family),
        )
        self._generator = TailwindComponentGenerator(self._current_ds)
        return self._current_ds

    def get_design_system(self) -> DesignSystem:
        return self._current_ds

    def generate_color_palette(self, primary: str, scheme: str = "light") -> dict[str, str]:
        try:
            scheme_enum = ColorScheme(scheme)
        except ValueError:
            scheme_enum = ColorScheme.light
        palette = ColorPalette.from_primary(primary, scheme_enum)
        return palette.to_dict()

    def generate_css_variables(self) -> str:
        return self._current_ds.to_css_variables()

    def generate_tailwind_config(self) -> str:
        cfg = self._current_ds.to_tailwind_config()
        return json.dumps(cfg, ensure_ascii=False, indent=2)

    # ── Component Generation ───────────────────────────────────────────

    def generate_component(
        self,
        component_type: str,
        params: dict[str, Any] | None = None,
    ) -> GeneratedComponent:
        p = params or {}
        type_map = {
            "button": (self._generator.button, ["variant", "size", "label", "outline", "full_width", "disabled", "with_animation"]),
            "card": (self._generator.card, ["title", "description", "image_url", "badge_text", "hover_effect", "horizontal"]),
            "navbar": (self._generator.navbar, ["brand", "links", "active_link", "with_search", "sticky", "transparent"]),
            "hero": (self._generator.hero, ["title", "subtitle", "cta_text", "cta_secondary_text", "with_image", "gradient", "centered"]),
            "stats": (self._generator.stats, ["items", "columns"]),
            "feature_grid": (self._generator.feature_grid, ["features", "title", "subtitle", "columns"]),
            "testimonial": (self._generator.testimonial, ["quote", "author", "role", "avatar_url", "rating"]),
            "pricing": (self._generator.pricing, ["title", "price", "currency", "period", "features", "popular", "cta"]),
            "form": (self._generator.form, ["title", "fields", "submit_text", "layout"]),
            "footer": (self._generator.footer, ["brand", "description", "columns"]),
            "modal": (self._generator.modal, ["title", "content", "confirm_text", "cancel_text", "size"]),
            "tabs": (self._generator.tabs, ["tabs_data"]),
            "avatar": (self._generator.avatar, ["src", "name", "size", "show_status", "status"]),
            "alert": (self._generator.alert, ["variant", "title", "message", "dismissible"]),
            "badge": (self._generator.badge, ["text", "variant", "size"]),
            "progress": (self._generator.progress, ["value", "label", "variant", "show_label"]),
            "table": (self._generator.table, ["headers", "rows"]),
            "stat_card": (self._generator.stat_card, ["label", "value", "change", "change_positive", "icon"]),
        }

        if component_type not in type_map:
            return GeneratedComponent(html=f"<!-- Unknown component type: {component_type} -->", component_type=ComponentType.custom)

        gen_func, param_names = type_map[component_type]
        kwargs = {k: p.get(k) for k in param_names if k in p}
        return gen_func(**kwargs)

    def generate_dashboard(
        self,
        title: str = "لوحة التحكم",
        stat_cards: int = 4,
        include_table: bool = True,
        include_chart: bool = True,
    ) -> GeneratedComponent:
        stats_html = ""
        for i, (label, val, change) in enumerate([
            ("إجمالي المستخدمين", "١٢٬٤٥٠", "+١٢.٥٪"),
            ("الإيرادات", "٨٩٬٢٠٠", "+٢٣.١٪"),
            ("الطلبات", "١٬٤٥٠", "+٨.٣٪"),
            ("الزيارات", "٤٥٬٢٠٠", "-٣.٢٪"),
        ]):
            pos = i != 3
            stats_html += self._generator.stat_card(label=label, value=val, change=change, change_positive=pos).html

        table_html = self._generator.table().html if include_table else ""

        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  {self._current_ds.to_css_variables()}
</head>
<body class="bg-gray-50 font-sans">
  {self._generator.navbar(brand="NOUFEX", links=[
    {{"label": "لوحة التحكم", "href": "#"}},
    {{"label": "التقارير", "href": "#"}},
    {{"label": "المستخدمين", "href": "#"}},
    {{"label": "الإعدادات", "href": "#"}},
  ], active_link="لوحة التحكم").html}
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="text-2xl font-bold text-gray-900 mb-2">{title}</h1>
    <p class="text-gray-500 mb-8">مرحباً بعودتك! إليك ملخص أدائك اليوم.</p>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 stagger-container">
      {stats_html}
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div class="lg:col-span-2">
        <div class="bg-white rounded-2xl shadow-sm p-6">
          <h2 class="text-lg font-bold text-gray-900 mb-4">آخر النشاطات</h2>
          {table_html}
        </div>
      </div>
      <div class="bg-white rounded-2xl shadow-sm p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">إحصائيات سريعة</h2>
        <div class="space-y-4">
          {self._generator.progress(value=85, label="المستخدمون النشطون", variant="primary").html}
          {self._generator.progress(value=65, label="معدل التحويل", variant="success").html}
          {self._generator.progress(value=40, label="المبيعات", variant="warning").html}
          {self._generator.progress(value=90, label="رضا العملاء", variant="secondary").html}
        </div>
      </div>
    </div>
  </main>
  <style>
    {AnimationEngine.get_css_package()}
  </style>
  <script>
    document.addEventListener('DOMContentLoaded', () => {{
      document.querySelectorAll('.stagger-container > *').forEach((el, i) => {{
        el.style.animationDelay = i * 0.1 + 's';
      }});
    }});
  </script>
</body>
</html>"""
        return GeneratedComponent(html=html, component_type=ComponentType.custom, framework=DesignFramework.tailwind)

    # ── UI Review ──────────────────────────────────────────────────────

    def review_ui(self, html: str, css: str = "", js: str = "") -> DesignReviewResult:
        return self._reviewer.review(html, css, js)

    def score_ui(self, html: str) -> int:
        return self._reviewer.score_html(html)

    # ── Animations ─────────────────────────────────────────────────────

    def get_animation_css(self, name: str | None = None) -> str:
        if name:
            for anim in AnimationEngine.list_all():
                if anim.name == name:
                    return anim.css
            return f"/* Animation '{name}' not found */"
        return AnimationEngine.get_css_package()

    def list_animations(self) -> list[dict[str, str]]:
        return [{"name": a.name, "description": a.description, "category": a.category}
                for a in AnimationEngine.list_all()]

    # ── Full Page Generation ───────────────────────────────────────────

    def generate_landing_page(
        self,
        brand: str = "NOUFEX",
        hero_title: str = "حلول ذكية لمستقبل أفضل",
        hero_subtitle: str = "نقدم أفضل الحلول التقنية المبتكرة",
        include_features: bool = True,
        include_stats: bool = True,
        include_testimonials: bool = True,
        include_pricing: bool = False,
        include_contact: bool = True,
    ) -> GeneratedComponent:
        sections = []
        sections.append(self._generator.navbar(brand=brand, sticky=True, transparent=True))
        sections.append(self._generator.hero(title=hero_title, subtitle=hero_subtitle))
        if include_stats:
            sections.append(self._generator.stats())
        if include_features:
            sections.append(self._generator.feature_grid())
        if include_testimonials:
            t_html = ""
            for t in [
                {"quote": "منصة رائعة! غيرت طريقة عملنا تماماً.", "author": "أحمد محمد", "role": "مدير تنفيذي"},
                {"quote": "أفضل منصة استخدمتها على الإطلاق.", "author": "سارة علي", "role": "مصممة UI/UX"},
                {"quote": "خدمة عملاء ممتازة ومنتج متكامل.", "author": "محمد خالد", "role": "مطور برمجيات"},
            ]:
                t_html += self._generator.testimonial(**t).html
            sections.append(f"""<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">ماذا يقول عملاؤنا</h2>
      <p class="text-xl text-gray-500">آراء العملاء هي دافعنا للتطوير المستمر</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">{t_html}</div>
  </div>
</section>""")
        if include_pricing:
            p_html = ""
            for plan in [
                {"title": "مبتدئ", "price": "٣٩", "features": ["مستخدم واحد", "مساحة ١٠ جيجابايت", "دعم أساسي"], "popular": False},
                {"title": "احترافي", "price": "٩٩", "features": ["مستخدمين غير محدود", "مساحة ١٠٠ جيجابايت", "دعم 24/7", "تقارير متقدمة"], "popular": True},
                {"title": "مؤسسات", "price": "١٩٩", "features": ["كل المميزات", "مساحة غير محدودة", "دعم VIP", "تكامل API"], "popular": False},
            ]:
                p_html += self._generator.pricing(**plan).html
            sections.append(f"""<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">خطط التسعير</h2>
      <p class="text-xl text-gray-500">اختر الخطة التي تناسب احتياجاتك</p>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">{p_html}</div>
  </div>
</section>""")
        if include_contact:
            sections.append(self._generator.form())
        sections.append(self._generator.footer(brand=brand))

        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{brand}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    {AnimationEngine.get_css_package()}
  </style>
</head>
<body class="bg-white font-sans antialiased">
  {"\n\n  ".join(sections)}
</body>
</html>"""

        return GeneratedComponent(html=html, component_type=ComponentType.custom)

    def generate_page_from_description(self, description: str) -> GeneratedComponent:
        desc_lower = description.lower()

        if "تسجيل" in desc_lower or "login" in desc_lower or "تسجيل" in desc_lower:
            return self._generate_auth_page()
        elif "لوحة" in desc_lower or "dashboard" in desc_lower or "تحكم" in desc_lower:
            return self.generate_dashboard()
        elif "هبوط" in desc_lower or "landing" in desc_lower or "تعريفي" in desc_lower:
            return self.generate_landing_page()
        elif "متجر" in desc_lower or "shop" in desc_lower or "منتجات" in desc_lower:
            return self._generate_shop_page()
        elif "مدونة" in desc_lower or "blog" in desc_lower:
            return self._generate_blog_page()
        elif "تواصل" in desc_lower or "contact" in desc_lower:
            return self._generate_contact_page()
        elif "بريد" in desc_lower or "email" in desc_lower or "إيميل" in desc_lower:
            return self._generate_email_template()
        elif "سيرة" in desc_lower or "cv" in desc_lower or "ذاتية" in desc_lower or "resume" in desc_lower:
            return self._generate_resume_page()
        else:
            return self.generate_landing_page()

    def _generate_auth_page(self) -> GeneratedComponent:
        html = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>تسجيل الدخول</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="min-h-screen bg-gradient-to-br from-primary/5 to-secondary/5 flex items-center justify-center p-4">
  <div class="w-full max-w-md">
    <div class="bg-white rounded-3xl shadow-xl p-8">
      <div class="text-center mb-8">
        <div class="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-2">NOUFEX</div>
        <h1 class="text-2xl font-bold text-gray-900">مرحباً بعودتك</h1>
        <p class="text-gray-500 mt-1">سجل دخولك للمتابعة</p>
      </div>
      <form class="space-y-5" onsubmit="event.preventDefault(); alert('تم تسجيل الدخول بنجاح!');">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">البريد الإلكتروني</label>
          <input type="email" placeholder="admin@noufex.ai" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"/>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">كلمة المرور</label>
          <input type="password" placeholder="••••••••" class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all duration-200"/>
        </div>
        <div class="flex items-center justify-between">
          <label class="flex items-center gap-2"><input type="checkbox" class="rounded border-gray-300 text-primary focus:ring-primary"/> <span class="text-sm text-gray-600">تذكرني</span></label>
          <a href="#" class="text-sm text-primary hover:underline">نسيت كلمة المرور؟</a>
        </div>
        <button type="submit" class="w-full py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 transition-all duration-300 active:scale-[0.98]">تسجيل الدخول</button>
      </form>
      <p class="text-center text-sm text-gray-500 mt-6">ليس لديك حساب؟ <a href="#" class="text-primary font-medium hover:underline">إنشاء حساب</a></p>
    </div>
  </div>
</body>
</html>"""
        return GeneratedComponent(html=html, component_type=ComponentType.custom)

    def _generate_blog_page(self) -> GeneratedComponent:
        posts = ""
        for i, (title, excerpt) in enumerate([
            ("كيف تبدأ مع NOUFEX", "دليل شامل لبدء استخدام المنصة والاستفادة من جميع المميزات"),
            ("أفضل ممارسات التصميم", "تعرف على أحدث اتجاهات وأساليب التصميم في 2026"),
            ("تحسين الإنتاجية", "نصائح وحيل لزيادة إنتاجية فريقك باستخدام الأدوات الذكية"),
        ]):
            posts += f"""<article class="bg-white rounded-2xl shadow-sm overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
  <img class="w-full h-48 object-cover" src="https://images.unsplash.com/photo-{(149975416, 1522071820081-009f0129c71c, 1519389950473-47ba0277781c)[i]}?w=600&q=80" alt="{title}"/>
  <div class="p-6">
    <div class="flex gap-2 mb-3"><span class="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full">تقنية</span></div>
    <h2 class="text-xl font-bold text-gray-900 mb-2">{title}</h2>
    <p class="text-gray-500 mb-4">{excerpt}</p>
    <a href="#" class="text-primary font-medium hover:underline inline-flex items-center gap-1">اقرأ المزيد <span>←</span></a>
  </div>
</article>"""

        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>المدونة</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-50 font-sans">
  {self._generator.navbar(brand="NOUFEX", with_search=True).html}
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-4xl font-bold text-gray-900 mb-4">المدونة</h1>
    <p class="text-xl text-gray-500 mb-12">آخر المقالات والأخبار</p>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">{posts}</div>
  </main>
  {self._generator.footer().html}
</body>
</html>"""
        return GeneratedComponent(html=html, component_type=ComponentType.custom)

    def _generate_shop_page(self) -> GeneratedComponent:
        products = ""
        for i in range(6):
            products += f"""<div class="group bg-white rounded-2xl shadow-sm overflow-hidden hover:shadow-xl transition-all duration-300">
  <div class="relative overflow-hidden">
    <img class="w-full h-56 object-cover group-hover:scale-105 transition-transform duration-500" src="https://images.unsplash.com/photo-{['1505740420928-5e560c06d30e', '1542291026-7eec264c27ff', '1523275335684-37898b6baf30', '1546868871-af0d1e5cf5a6', '1485955892927-57d6b1e2e28a', '1491553895911-0055eca6402d'][i]}?w=400&q=80" alt="منتج"/>
    <span class="absolute top-3 right-3 bg-error text-white text-xs font-medium px-2 py-1 rounded-full">تخفيض</span>
  </div>
  <div class="p-5">
    <h3 class="font-bold text-gray-900 mb-1">منتج رقم {i+1}</h3>
    <p class="text-sm text-gray-500 mb-3">وصف مختصر للمنتج</p>
    <div class="flex items-center justify-between">
      <span class="text-lg font-bold text-primary">٢٩٩ ريال</span>
      <button class="px-4 py-2 bg-primary text-white text-sm rounded-xl hover:bg-primary/90 transition-all">أضف للسلة</button>
    </div>
  </div>
</div>"""

        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>المتجر</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-50 font-sans">
  {self._generator.navbar(brand="NOUFEX", with_search=True).html}
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="flex items-center justify-between mb-12">
      <div><h1 class="text-4xl font-bold text-gray-900">المتجر</h1><p class="text-gray-500 mt-2">أحدث المنتجات والتخفيضات</p></div>
      <div class="flex gap-2">{self._generator.badge(text="تخفيضات تصل إلى ٥٠٪", variant="error").html}</div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">{products}</div>
  </main>
  {self._generator.footer().html}
</body>
</html>"""
        return GeneratedComponent(html=html, component_type=ComponentType.custom)

    def _generate_contact_page(self) -> GeneratedComponent:
        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>تواصل معنا</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-50 font-sans">
  {self._generator.navbar(brand="NOUFEX").html}
  <section class="py-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
        <div>
          <h1 class="text-4xl font-bold text-gray-900 mb-4">تواصل معنا</h1>
          <p class="text-xl text-gray-500 mb-10">نحن هنا لمساعدتك. اختر الطريقة المناسبة للتواصل.</p>
          <div class="space-y-6">
            <div class="flex items-center gap-4 p-4 bg-white rounded-xl shadow-sm"><div class="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary text-xl">📧</div><div><div class="font-bold text-gray-900">البريد الإلكتروني</div><div class="text-gray-500">support@noufex.ai</div></div></div>
            <div class="flex items-center gap-4 p-4 bg-white rounded-xl shadow-sm"><div class="w-12 h-12 bg-secondary/10 rounded-xl flex items-center justify-center text-secondary text-xl">📞</div><div><div class="font-bold text-gray-900">رقم الجوال</div><div class="text-gray-500" dir="ltr">+966 55 123 4567</div></div></div>
            <div class="flex items-center gap-4 p-4 bg-white rounded-xl shadow-sm"><div class="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center text-accent text-xl">📍</div><div><div class="font-bold text-gray-900">العنوان</div><div class="text-gray-500">الرياض، المملكة العربية السعودية</div></div></div>
          </div>
        </div>
        <div>{self._generator.form(title="أرسل لنا رسالة", fields=[
          {{"type": "text", "label": "الاسم", "placeholder": "اسمك", "required": True}},
          {{"type": "email", "label": "البريد", "placeholder": "بريدك", "required": True}},
          {{"type": "text", "label": "الموضوع", "placeholder": "عنوان الرسالة"}},
          {{"type": "textarea", "label": "الرسالة", "placeholder": "اكتب رسالتك...", "required": True}},
        ]).html}</div>
      </div>
    </div>
  </section>
  {self._generator.footer().html}
</body>
</html>"""
        return GeneratedComponent(html=html, component_type=ComponentType.custom)

    def _generate_email_template(self) -> GeneratedComponent:
        html = """<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>البريد</title></head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:'Segoe UI',Tahoma,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:40px 20px;">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
      <tr><td style="background:linear-gradient(135deg,#3B82F6,#8B5CF6);padding:40px;text-align:center;">
        <h1 style="color:#ffffff;font-size:28px;margin:0;">NOUFEX</h1>
        <p style="color:rgba(255,255,255,0.9);margin-top:8px;">منصة الحلول الذكية</p>
      </td></tr>
      <tr><td style="padding:40px;">
        <h2 style="color:#1f2937;font-size:22px;margin:0 0 16px 0;">مرحباً بك! 👋</h2>
        <p style="color:#6b7280;line-height:1.8;margin:0 0 24px 0;">شكراً لتسجيلك في منصة NOUFEX. نحن متحمسون لانضمامك إلينا!</p>
        <table role="presentation" cellpadding="0" cellspacing="0"><tr><td style="background-color:#3B82F6;border-radius:12px;padding:12px 32px;">
          <a href="#" style="color:#ffffff;text-decoration:none;font-size:16px;font-weight:600;">تأكيد الحساب</a>
        </td></tr></table>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0;">
        <p style="color:#9ca3af;font-size:12px;text-align:center;">إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذه الرسالة.</p>
      </td></tr>
      <tr><td style="background-color:#f9fafb;padding:24px;text-align:center;">
        <p style="color:#9ca3af;font-size:12px;margin:0;">© 2025 NOUFEX. جميع الحقوق محفوظة.</p>
      </td></tr>
    </table>
  </td></tr></table>
</body>
</html>"""
        return GeneratedComponent(html=html, component_type=ComponentType.custom)

    def _generate_resume_page(self) -> GeneratedComponent:
        html = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>السيرة الذاتية</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-gray-100 font-sans py-12">
  <div class="max-w-4xl mx-auto px-4">
    <div class="bg-white rounded-3xl shadow-xl overflow-hidden">
      <div class="bg-gradient-to-l from-primary to-secondary p-8 text-white text-left">
        <div class="flex items-center gap-6">
          <div class="w-24 h-24 bg-white/20 rounded-2xl flex items-center justify-center text-4xl">👤</div>
          <div><h1 class="text-3xl font-bold">أحمد محمد</h1><p class="text-white/80 text-lg mt-1">مطور واجهات أمامية</p></div>
        </div>
      </div>
      <div class="p-8 grid grid-cols-3 gap-8">
        <div class="col-span-1 space-y-6">
          <div><h3 class="font-bold text-gray-900 mb-3">معلومات الاتصال</h3><div class="space-y-2 text-sm text-gray-600"><p>📧 ahmed@email.com</p><p>📞 +966 55 123 4567</p><p>📍 الرياض</p></div></div>
          <div><h3 class="font-bold text-gray-900 mb-3">المهارات</h3><div class="flex flex-wrap gap-2"><span class="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full">React</span><span class="px-3 py-1 bg-secondary/10 text-secondary text-sm rounded-full">TypeScript</span><span class="px-3 py-1 bg-accent/10 text-accent text-sm rounded-full">Tailwind</span><span class="px-3 py-1 bg-info/10 text-info text-sm rounded-full">Next.js</span></div></div>
        </div>
        <div class="col-span-2 space-y-6">
          <div><h3 class="font-bold text-gray-900 mb-3">الخبرات</h3>
            <div class="space-y-4">
              <div class="border-r-2 border-primary pr-4"><h4 class="font-bold">مطور واجهات</h4><p class="text-sm text-gray-500">شركة تقنية • 2022 - الآن</p><p class="text-sm text-gray-600 mt-1">تطوير واجهات مستخدم باستخدام React و Next.js</p></div>
              <div class="border-r-2 border-gray-200 pr-4"><h4 class="font-bold">مطور مبتدئ</h4><p class="text-sm text-gray-500">شركة برمجيات • 2020 - 2022</p><p class="text-sm text-gray-600 mt-1">تطوير وتصميم مواقع إلكترونية</p></div>
            </div>
          </div>
          <div><h3 class="font-bold text-gray-900 mb-3">التعليم</h3><div class="border-r-2 border-primary pr-4"><h4 class="font-bold">بكالوريوس علوم حاسب</h4><p class="text-sm text-gray-500">جامعة الملك سعود • 2016 - 2020</p></div></div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>"""
        return GeneratedComponent(html=html, component_type=ComponentType.custom)
