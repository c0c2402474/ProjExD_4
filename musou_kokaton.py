import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx - org.centerx, dst.centery - org.centery
    norm = math.sqrt(x_diff**2 + y_diff**2)
    return x_diff / norm, y_diff / norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }


    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"
        self.hyper_life = 500

    """
    追加機能4
    """
    def infinity(self, key_list: list[bool], screen: pg.Surface):
        self.image=pg.transform.laplacian(self.image, self.state, self.hyper_life)




    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        if key_lst[pg.K_LSHIFT]:
            self.speed = 20
        else:
            self.speed = 10

        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed * sum_mv[0], self.speed * sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed * sum_mv[0], -self.speed * sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state=="hyper":
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life = self.hyper_life -1
            if self.hyper_life<0:
                self.state="normal"
                self.change_img(3,screen)

        screen.blit(self.image, self.rect)
        """
        画像imageを変換したものに切り替える
        • hyper_lifeを1減算し,0未満になったらstate="normal"とする
       
        """


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2 * rad, 2 * rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery + emy.rect.height // 2
        self.speed = 6
        self.state = "active"  # 爆弾の状態 ("active", "inactive")

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if self.state == "active":
            self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
            if check_bound(self.rect) != (True, True):
                self.kill()
        elif self.state == "inactive":
            self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
            if check_bound(self.rect) != (True, True):
                self.kill()
            self.speed *= 0.9  # 徐々に減速


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird,angle0: int=0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle + angle0)) 
        self.vy = -math.sin(math.radians(angle + angle0))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class NeoBeam(pg.sprite.Sprite):
    def __init__(self, bird: Bird, num: int):     
        self.bird = bird
        self.num = num
    def gen_beam(self):
        lst = []
        for i in range(-50, +51, self.num):      
            lst.append(i)
        return lst


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """

    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life // 10 % 2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image_orig = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.image = self.image_orig
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT // 2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル
        self.can_attack = True  # 攻撃可能フラグ

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Gravity(pg.sprite.Sprite):
    """
    重力上に関するクラス
    """
    def __init__(self, life: int):  # イニシャライザの引数を発動時間の変数life
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))  #画面全体の画像
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, WIDTH, HEIGHT))
        self.image.set_alpha(128)  # 透明度
        # self.image.fill((0, 0, 0))  # 黒い矩形
        self.rect = self.image.get_rect()
        self.life = life

    def update(self):
        """
        lifeを1減算し,0未満になったらkillする
        """
        self.life -= 1
        if self.life < 0:
            self.kill()

class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """

    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT - 50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class EMP:
    def __init__(self, enemies:pg.sprite.Group, bombs:pg.sprite.Group, screen:pg.Surface):
        self.enemies = enemies
        self.bombs = bombs
        self.screen = screen
        self.active = False

    def activate(self):
        if not self.active:  # すでにアクティブでない場合のみ発動
            self.active = True
            self.disable_enemies()
            self.disable_bombs()
            self.display_visual_effect()

    def disable_enemies(self):
        for enemy in self.enemies:
            enemy.image = pg.transform.laplacian(enemy.image)  # ラプラシアンフィルタを適用
            enemy.interval = float('inf')  # 無限大に設定

    def disable_bombs(self):
        for bomb in self.bombs:
            bomb.speed /= 2  # スピードを半減
            bomb.state = "inactive"      # 非アクティブに設定

    def laplacian(self, image):
        # ラプラシアンフィルタを適用する処理
        return pg.transform.rotozoom(image, 0, 0.9)  # 例として縮小処理を適用

    def display_visual_effect(self):
        overlay = pg.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)  # 透明度を設定
        overlay.fill((255, 255, 0))  # 黄色
        self.screen.blit(overlay, (0, 0))
        pg.display.flip()
        pg.time.delay(50)  # 0.05秒待機



class Shield(pg.sprite.Sprite):
    """
    防御壁クラス
    爆弾と衝突、あるいは発動後400フレームで消失
    こうかとんの向いている方向に生成
    """
    def __init__(self, bird: Bird, life: int = 400):
        super().__init__()
        self.life = life

        self.width = 20  #シールドの横幅20
        self.height = bird.rect.height * 2  #シールドの高さ：こうかとんの身長の2倍
        shield_surface = pg.Surface((self.width, self.height)) 
        shield_surface.set_colorkey((0, 0, 0))  #黒を透過色に設定
        pg.draw.rect(shield_surface, (0, 0, 255), (0, 0, self.width, self.height))  #青いシールドを生成

        vx, vy = bird.dire  #こうかとんの向きを取得
        self.angle = math.degrees(math.atan2(-vy, vx))  #vx,vyから角度を計算
        self.image = pg.transform.rotate(shield_surface, self.angle)  #self.angleの角度だけシールドを回転
        self.rect = self.image.get_rect()

        #向いている方向に、こうかとんの中心からこうかとん１体分ずらした位置にシールドを設置
        self.rect.centerx = bird.rect.centerx + vx * bird.rect.width
        self.rect.centery = bird.rect.centery + vy * bird.rect.height

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()

    
def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    emp = EMP(emys, bombs, screen)
    gravitys = pg.sprite.Group()
    neobeam = NeoBeam(bird,5)
    shields = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0 
            
                #追加機能4
                #発動条件が満たされたら,state="hyper", hyper_life=500とする.消費条件スコアscore.valueは最終的に100にする
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value>100:
                bird.state="hyper"
                bird.hyper_life=500
                score.value=score.value-100
            

            # if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            #     beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and key_lst[pg.K_LSHIFT] and event.key == pg.K_SPACE:
                beam_lst = neobeam.gen_beam()
                # print(beam_lst)
                for i in beam_lst:
                    beams.add(Beam(bird, i))
                    



            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                emp.activate()
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and score.value >= 200:  # gravity発動条件
                gravitys.add(Gravity(400))
                
                score.value -= 200  # 200点ダウン
            if event.type == pg.KEYDOWN and event.key == pg.K_s:  #sキーを押下したとき
                if score.value >= 50 and len(shields) == 0:  #スコアが50以上かつシールドが場にないとき
                    shields.add(Shield(bird))
                    score.value -= 50  #シールドを展開する度にスコア50を消費
        screen.blit(bg_img, [0, 0])



        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())



            

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0 and emy.can_attack:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            """
            追加機能4こうかとんと爆弾の衝突判定で,state="hyper"なら
            ゲームオーバーにならずに爆弾を爆発させ,スコアを1アップさせる
            """
            if bird.state=="hyper":
                score.value += 1
            else:    
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                pg.display.update()
                time.sleep(2)
                return
            score.update(screen)
            pg.display.update()
        
        for shield in pg.sprite.groupcollide(shields, bombs, True, True).keys():  #シールドと爆弾の衝突判定
            exps.add(Explosion(shield, 50))
        for gravity in gravitys:
            for bomb in pg.sprite.spritecollide(gravity, bombs, True):
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                bird.change_img(6, screen)
        
        for gravity in gravitys:
            for emy in pg.sprite.spritecollide(gravity, emys, True):
                exps.add(Explosion(emy, 50))  # 爆発エフェクト
                bird.change_img(6, screen)

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        gravitys.update()
        gravitys.draw(screen)
        score.update(screen)
        shields.draw(screen)
        shields.update()
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()  