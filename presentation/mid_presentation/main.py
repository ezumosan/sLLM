from manim import *
from manim_slides import Slide

class MathPresentation(Slide):
    def construct(self):
        # 1. 日本語テキスト（Textクラスを使用し、画面上部に配置）
        title = Text("sLLM - 小型大規模言語モデルにおけるオーケストレーションを用いたハルシネーション抑制の研究", font_size=36).to_edge(UP)
        
        # 2. 数式（MathTexは英数字・LaTeX記号のみにする）
        eq1 = MathTex(r"f(x) = x^2")
        
        self.play(Write(title))
        self.play(Write(eq1))
        
        # クリック待ち
        self.next_slide()

        # 3. 次のステップ（微分の変形）
        eq2 = MathTex(r"f'(x) = 2x")
        self.play(Transform(eq1, eq2))
        
        self.next_slide()
        
        self.play(FadeOut(eq1), FadeOut(title))