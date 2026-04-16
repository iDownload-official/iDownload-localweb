import yt_dlp
import yt_dlp_ejs
from flask import Flask, send_file
import socket
import threading
import subprocess
import os
import time

script_dir = os.getcwd()

hostname = socket.gethostname()
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))   # doesn't actually send data
    IPAddr = s.getsockname()[0]
    s.close()
except:
    print("Error 01: It is most likely that you do not have a WiFi connection.")
    input("")
    quit()

isDownloading = False
finalFile = ""

class Logger:
    def debug(self, msg):
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)
    def info(self, msg):
        global message
        print(msg)
        message = str(msg).replace("[0;94m", "").replace("[0m", "").replace("[0;32m", "").replace("[0;33m", "").replace("[download]", "").replace("[youtube]", "INFO:").replace("[info]", "INFO:")
    def warning(self, msg):
        print(msg)
    def error(self, msg):
        print(msg)

def Phook(d):
    if d['status'] == 'finished':
        print('Done downloading, now post-processing ...')

# https://www.youtube.com/watch?v=6KhC2r6AjLc

homepage = """<!DOCTYPE html>
<html>
    <head>
        <title>iDownload-localweb</title>
        <link href='https://fonts.googleapis.com/css?family=Roboto:400,700,600' rel='stylesheet'>
        <style>
            body {
                background-color: #191919;
                color: #e7e7e7;
                font-family: Roboto;
            }
            .main-flexbox-container, .start-button-flexbox-container, .finish-button-flexbox-container {
                display: flex;
                flex-direction: row;
                justify-content: space-evenly;
            }
            .url-input {
                font-size: 4vh;
                width: 100%;
                background-color: #191919;
                border-style: solid;
                border-color: #e7e7e7;
                border-width: 2px;
                border-radius: 4px;
                color: #e7e7e7;
            }
            .main-flexbox-item {
                width: 60vw;
            }
            button {
                font-size: 4vh;
                background-color: #191919;
                border-style: solid;
                border-color: #e7e7e7;
                border-width: 2px;
                border-radius: 4px;
                color: #e7e7e7;
                cursor: pointer;
            }
            .-yt {
                border-color: #FF0000;
                color: #FF0000;
            }
            .bbc {
                border-color: #FF4C96;
                color: #FF4C96;
            }
            p {
                font-size: 4vh;
            }
            h1 {
                font-size: 6vh;
            }
        </style>
        <script>
            let inputURL
            let inputID
            let endpointURL
            let response
            let text
            let repeatFunction1

            async function updateStatus() {
                response = await fetch("/status");

                text = await response.text();
                document.querySelector(".download-status-text").innerHTML = text;

                if (document.querySelector(".download-status-text").innerHTML == "Ready to download!") {
                    document.querySelector(".finish-button-flexbox-container button").style.display = "flex";
                    clearInterval(repeatFunction1);
                } else {
                    document.querySelector(".finish-button-flexbox-container button").style.display = "none";
                };
            };

            async function startYTDownload() {
                repeatFunction1 = setInterval(updateStatus, 1000);
                inputURL = document.querySelector(".url-input").value;
                inputID = inputURL.split("=")[1];
                endpointURL = ["/ytdownload/", inputID, "/1080"].join("")

                response = await fetch(endpointURL, {method: "GET",});
            };

            async function startBBCDownload() {
                repeatFunction1 = setInterval(updateStatus, 1250);

                inputURL = document.querySelector(".url-input").value.replaceAll("/", "~");
                endpointURL = ["/bbcdownload/", inputURL, "/1080"].join("")

                response = await fetch(endpointURL, {method: "GET",});
            };

            updateStatus()
        </script>
    </head>
    <body>
        <div class="main-flexbox-container">
            <div></div>
            <div class="main-flexbox-item">
                <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAABaWlDQ1BJQ0MgUHJvZmlsZQAAKM99kLFLAmEYxh+tEMqGqMGh4aZouEo0yKVBDaQIOqwgazrPUwO9Pu4uwmiL1hD6DzJoDhqSCIOWhoYgaoiorcmpoKXk6/3uLrSh3o+X78fD87y8vIA/pDJW6gZQNmwznUpIK5lVKfAKHz2nVM1icUWZF/zz/66PB9d7NyZmNVu1/dhe6qp8erGw/RiawP/Vm9Mtjf4v6rDGTBvwycTKls0E7xAPmbQUcVVwweUjwVmXzxzPUjpJfEMsaUU1R9wklrMdeqGDy6VNzdtBbB/UjeVFMYd6GDNYhwWGElRUIEFB9A//pONPYoPcFZiUK6AImzJxUsQEnXgWBjSMQyaOIEwdEXf27nfv3U9ua7svwHSDc37e1uYawMkUnaze1kZjwEAfcF1nqqk6Uhe1P58H3o6B/gwweEuZNSsfjbjbBxNAzzPn7yNA4ABoVTn/POS8VaPwE3BpfAMXKWq85kk3lgAAAAlwSFlzAAAOwwAADsMBx2+oZAAAABh0RVh0U29mdHdhcmUAUGFpbnQuTkVUIDUuMS4y+7wDtgAAAIxlWElmSUkqAAgAAAAFABoBBQABAAAASgAAABsBBQABAAAAUgAAACgBAwABAAAAAgAAADEBAgAQAAAAWgAAAGmHBAABAAAAagAAAAAAAABgAAAAAQAAAGAAAAABAAAAUGFpbnQuTkVUIDUuMS4yAAIAAJAHAAQAAAAwMjMwAaADAAEAAAD//wAAAAAAAKuM8Tfp06LXAAAbuElEQVR4Xu2deXhURbr/v1XndGftbJ0FwiphVVQWxwFXkkYdRIROZByXueMCjsvIVa/y02FTAbcZnauIiuJyXUa9QNrRq+Mo6WQcdwQUlxEwEMKWdHpLdzq9nOX9/dENxEOATqcTupt8nuf8U/XWSfrU91S9VW9VHaCPPvroo48++uijjz766CPpqa6wGaorbHna9D4Oh2sTUgLGlqskfr2u3Dlbm9XHz2HahGRnXYV9vMDVz4tyG/RO70AEQpn/4FxZUGU1btTa9pGCLYCqisuMObv1Jw9cjPHDVqG/8aeLGOjzNVNcK6srWvpr7U90UqoFWFfuNItCqHpC2bPISv/q4M9ztv0KDbYKuL3FNjB6QOTBp2fV9A9py5+IpIwALKbmDFlJ23BSv69OKSt5FCrlRHIInLVBUY1ocs/ErpYz0R7I+ZozZWFVrfFdzW1OOFKmC1AU/a1Z6a2nDDS+BUJGhxwGlQxgzI8BBasxcdhjGFqyeZwgyP+3ZorbUl1hH9vB+IQjJVqA6gr7IJX45pMHf2Dsn/cSVMrVmhyEsRAYAvAGzkWDbRpa3IMDKvEnRS4/ZLYWObT2qU5KCGDNFNdzBTlNc04fshSMSVE1bJy1g0gHe9t0NDSfj1afcQ9jdL9e8Lxw6fqhitY+VUl6AayrcExmUD8eN+wNnp/1PlTK1pocBQJnXshqf+x3zUKjbQL8oezPOVMWVNUarVrrVCTpBbBmits6oHBr+egBy0CUEdNPYlDAmBd+6XQ02i/FfsdIyIr+dYHLSyqthdu19qlE159WArG23HmVXgy8OnH4U8jQfwuidK1Jl2AsCAYJre3laLBdBLtngBfE/iII0qPmmmKP1j4VSFoBWEy2HFnRbRxe+vnwoUWPH9Xx6yqc+aBSJlo8l6DBdg687fn1jNG9l9UWvKq1TXaO7S0lKIqiu8OQ6R4+oOAtEGVps7uFSlkACCW5f8WEYQ9jeOnnZXox8MqaKe7adRWOs7T2yUxStgDVFfbhKvFNY4e8ayjJfS2ub78WBhmM+dAeOgO7Wi5Bk7NMVVTxRYHL91daixq19slGUgpgzRT3a4W5u688bchSANQrDRljAQAq3L4LsNM2FS5vPyfAHhF4aIW5pqRda58sJJ0A1pU7yjlXrOOHvYLczNpIc91bEDjzQVFzYPPMRINtMnz+3B84UxdV1RZUa62TgaQSwP9duIv7Q7kfDyr6bvKo0ge7OOaPJyo48yIkD8ce5yzsaRmLkJz+d87lhVXWwk1a60QmqQSwttw5J03nf25i2eNI128DUZrWpFdhTAJDO9qCk7HLNh3N7qGSqgqrBC4vr7QWNWntE5GkEYClwmaUVd3mkQP/NWiwcSVUSpwVX4z5AXA4236Fnc3laG0rbgaj5aIQeGbW+lJJa59I9Lz3FCdkVTc/N8sxqDTvLRAZtNnHFaIMEOlhzH4b405ajlGDrCUZet8Tkpz5xbpyxzStfSKRFC1AdYX9FCK24dST3sooMqztEOtPRBRw1oaANAa7HTOxzzEGkpxWLXB5UaW18Aet9fEmKQSwdorL0q+gftbJg+6PTPcm/r8dDjsH4fGfi4aWabC7B/lV4itEQXrYXFPs1NofL2J+khaT7XwC/70KXU8urVIFhHJUlVeVFm5FWcn/QCfsgkqGpOm9OGuHSno4vNPRYDsPrT5jI2O0NE3nfmHGB8NUrX1vE7MAqk2OG0XyP52j1kcmY2K+1REgqNDBI5SBID6kqHxaVrrn9CHFn6E4920IzBOZA4j33+0JImFnpT/2uc1otE1AIJT1WSTsXKu17k1ifnprTa1zs2jfs8ODY8AiEognDIDELsZ2/SqEWM5Ekfm+keWM+WB0V4GhKX9o8YfIy1oPgHc7CthbHJhW9ociYWfnCMiK/rVI2Llea98bdFMA+58dFvw1GLwAdFqTbsHghsTK8ZP+UUgs+5yqmrxPAKC6omWIoopLBC5f06/gJzak6B1k6jeBKAsEUXubhORQ2LkCO20XwuEZ4AGxxwRBesxcU+zV2vckcehIY9ZQTFRai3bNrsu/jsDP22sf89HG+j9gl30eZNUIzjwAjnu3ekyI0qBSNnIza3HakKUYO+TdnOxM972yotu0ttx5pda+J4mDAI4PVVbjx7Pr8s4PSem/27538s5NO+6GzfMbIBLPTwYOhZ1fw4RhD2F46RfD9WLwtTVT3DXrKhyTtPY9QdIK4ACX1Ra8LArS+Lb2/GXfNcxo+7ZxEVr954OzNjDWkwOUeMGhUi5EbsfQov/GhLKnMKBwawUDfbJmiuvZ6oqWQdoS8STpBQAA5pri1svq8hcxpk5scQ9+c3P977Bt/90ISsPBmRsMib/IlyBCpVxkpm3B6AHLMG7Y67zA0DRXJWHz2nLXXRZTc8fNDnEjJQRwgEpr4bbZdXm/UVXhgkbbqV9urP9P7HbcDIUMEf+AACIg5Af53KA2R/jyuYGQH6Dj7z8QpYMoA/lZ7+P0oUsxZtCHxsw0zyOykrZhXbnTrLXvLjF7cIdGAZeDwdNro4BoeXvqHiGkZM4hYotys+0DhhbVIZ+/A56phzByAsQhI8BywwElanVD3rUdyrbNIL8XLCMHYDE/mjgSDjsH5RHY45iJvfaxCMnp73EuL6iyFn6ttY6FmH9logvgAG9d3FIUaBTvEjOVuePn2fKGmLIhFJcCXPi5oapCtjUh8GkdQuvXhAUg6n9uc5wIh539aAtMRkPLdNjcQ0KqKjwjcPmBSmtRs9a+K6S8AACAiPTtLrUmI5+fE80PDm3/N3wvPQ5yNgH6xJlkOhR2nhYJOxft51xZzpjyYqzL0lLKB+gMIsoG8EFmlJUPAPoRY2C4ZSFYfgkgJ044/1DY+W8Yd9IyjBpU11/gypNEwp+1ttGS8gIAsALA+drEYyGWDkTmb/8AKFLYcUwYwrudRd4MQ/oOqMRUAntDaxUtKS0AIroQwDXa9GhJG3MqdOfNBAV6dXY2ClQoqhH1zRdDVnQvVFmNH2ktoiWlBQBgnjbhAKQoCO7fh+D+fSDlyPME6WeVgwm6hGoFOPOi2TMTLm+JQ+Dy/dr8rpCyAiCiUgBna9MBQHK7sPdPy9E4YxwaZ4zD3j8th+R2ac0AAGL/AeCDRoe7ggSAMQlBeTh2NU8CiD1SaS3arbXpCikrAABlADpdOWp7+QX47lkC6A2A3gDfPUtge/kFrRkAgKWlQRwwAExJjL2hDH7sccyCL5D7vSCEVmjzu0oqC6BImwAAsteDQN374GeUAlwEuAh+RikCde9D9nZeyS1iBXztZ4CzVjDI2uxeg7HwXMBe+1hwpi4y15T4tTZdJZUF0OkAnmQZFGgPV/4BuAgKtIPkzivXk1a2/6tv5mGX/VbIasFxCjuHt8A1tExHSE5/r6q2wKK1iIVUFkDcGDsr/e7WLWmXb997VsPmHXfD5rk8sswrprmXmOCsDc62abC5h4Q4lxdq82OlTwBRIIhMugaF/ytyabynveCB7xpm+L5tXAyP/1xw5u2FsLMCWS3EzuZyqKrwTJW1cLPWIlb6BBAdDADM1mL37Lr8BYzRxBb34P/dVH9NJOxc1qNhZ87a0OSehda2oiaByw9o87tDnwBioNJauHV2Xd7lqipc1Gg7bcPG+tuwx3ETFMoGZ964LpFlLISAdDIabb8AGC3vbvBHS58AukFVrfEDveg7KxDKvPnHPefv+3rnAti9s8AgRQI33YchiN2OmWgPGjaJPLhKm99d+gTQTWauHyBfVlvwtMDlce62wr9saagKfr9nEdoCZ4IzT+TcwtjgrB0e/3nY5xgNzpQFs2r6x36zI9AngDhRaS1qmV2XfwdAv2xyDntnc/0c1DffhZA8EJy1xjBsJKikR4PtV5DktHVVtcb3tRbxoE8AcabKWvjN7Lq8S2VFP2tn04RvN9XfiX2u60CkB2dtUfsHnHnh8E6HvXVQu8Dlxdr8eJHKAojn2KzL96qqLfibKATObA8a7vx341T7Nw2L4PRNA2OByHlDR4ZBhqSUYqftPKjEV/TkruKUFAARmQBcp03vBjOJaLg28ViYa/oFLqvNf5RzZZzTW7Lqmx2/Uf69ZyHag6cfdVqZMR/2u2bB4zM2Clx6RJsfT1JKAEQ0nojqAKwHEM+DGa4G8B0RPU4xnE5RaS3aO7su/0YCO3ufY+T6TfU3Yaftdkhq8WH+AWNB+EPj0NgyAYzRfZXWnt1KnjICIKJKAB/HsvonStIi6wusRDRQmxkNVVbjF7Pr8i4IyWlX1O8/c9um+vloav0tAB7ZzURgkNFon4FAKOvTdNH5ovYe8SYlBEBEFQDeAJCpzesBzgDwViwtwQEuqy14QxRCE33+vMXf75rWumXXIrjbTRC4Da3t5djvHAnOlAWXfDg8Oo+xGyS9AIgoF8CquC9LPjoTASzXJnYFc01J22V1+Us5UyfYWwe+8vWOq7F131LsaJ4GRRFfrao11mnL9ARJLwAANwDosoMWB24gojHaxK5SaS3cMbsu7z9UlU/abRv7ubutxCMI0iKtXU+R1AIgIjHioHVK+/ZtaH75BTS9+Bx8Px4YSR15cTjjAkiR4fqnFftXPQn72xZIriP6YGkAwtuR4wDnjAQRYAyM6Cj/ZJxJagFE3vzR2kQA8GzcgD3TRsE973q03nkD9l58Cly1NWCcAcLhB0mw9EzInlbsW/EX2KaY4F16KxwzK7Fn/ryjiWCKNqGrWEz2kyxT3S8ByheKf9MkVd5rYFzXrYWeXSHZBTAEwGH7t9RQCM7/eQ7QAXzsKPAxI8GKB6Pltktgf2sdmC4N4B1+uqADBf1oemQpfCvng589EmzoSPBzRiG0+jW0fnTE7ngQxXhWfXVFc5ZlqmsBGN+kSrt+F3Q9gaDTBMn7OkDS1RaTo9viioZkF0CnXr8a8EPZtR3MMPDQ1KuYDpY1AJ6H50C1NQBCB91wAeRqQujjdWAlIw+lE4ENBEL79hxK+zlpsTifFpPz14ynbSTFtUzyrMkL2i+EGlgKxo1QAw9CCX4PMGH5m+dt7/H66fE/0MO0ahMAQMjKhn78ZFDTnp/v8uUCWMHIzv0ALoBladeRMtAeIGP0yZr0g/gAHH1etwMWk+MXlqnuD0CBN2XfP0cF7TdAbvt9+DasHxA540jyrgapbWfp9YXXau8Rb5JdADsAtGkTmSCg8Lrfg592Dqh1R2xbvRmD+v1WZD10P3LPPlebe4Dt7FgT+wAsppZSy1T3UwB9qgS/vyDovA9S60yQuj5S8eGjYgAArB9Ieg1y+ycA2GKLqaVAe794ktQCYIw1APhKmw4AGYOHoPQvz4MPmAjyNHRNBIxB/XErMu9YiP633gGuP+Kp5B9oEzpSXdGUZpnquh1M/FqV9t4Ucq8SQ46zoYZWAawEQEkn0UECGIPc9ihItg0G083XGMSVpBUAEZUR0SMAjjgWzxwxEqVPvAReOj56ERyo/HkLUXrH3RAyj+rj3UpEfyKiMm2GxeScwXj6l6S0PiZ5/1YUdJih+BcAzBh5649GCaB+Ccn3HkDKPIvJfsQ+qLskpQCI6A4AmwHcFXmNjkjmiFHRi0Bb+VlHrXxEdh/dCWAzEd0OAG8aW8Zaprr/BoTelts/Oy3omAfZew1AjR36ee1br4UAlg+l/Tao0s4MMHGp1iJeJIcAOtQZEa0E8CiAqOfifyaC1iOIoOuV3xEDgMdcu6WPdKPUT5X2bZcGnQ9Cck8DyW9HKj43iorvSBpAgOT9K0DBSovJGc/o5kGSQwAUfnJEtADAzdrsaDgoggHjQa6tGhEwqN/FXPkHyRsonjtm8V5D+6dnQg0+Hu7nWWf9fDQQwIqhBh+DHPgGYHxZdfm+Lg85j0XiC4ABnho1RESjAXRraVTmiFEoXfkqxNMuBTVuDZ8KpipQt21F1oLlGHDnH2Ou/AOMNJ2Cfvf8F5S4fHA2LFLZ+wxIaZ3AhIwbtRbdJfEFQIAUfoXu6GzW7wAkSVAD/mNeGYMHo/ThFTDc8wRYejZYeiZyH3wG/ebeDIjCYfadXSQdeXEuF/UY8+urQFJ4IqnbsH4guRpy+0cA8MfqipZjeZBdopPOMDp665Co7eqf1aKr8isn35y1AsBhp2aqUgjOv7+LNus/QD5vVK0tywifuShv2wIAEEecFj4kQopi6R8DWJYB2RUXoWDadHDd4ZoM+Xx477or4fv8bXDDUX3UKHEBbATSjGvBdf1XmNfnHfHgi66S8ALY6vlz6NSVRfeWnZN2/8Gpsg7Y3nwNzt9cDT5WAHRd+IIoE8HSw5+eoYAHoM7X53WK1Ar1OwUFb7yK4suv0uYCAP758ANovHsBxFPiIQAGUBOEzIegz50jAWySucYYl8/TJXwXQH5S0wxsYGeVL3s98L7xIoQz+oPlloFlFkZ/ZeQBjAOMg2XkHZ5/tCu3DMIZ/eF948UjnimQ1b80msYoSghgRijtd0MJbdeBCcu0FrGS8AJAeISmOdUxDMkKyN8G8Pi2PlHBdSB/G0jufEMoEzv9l7tB+DfK3lcA1T/NYnJWai1iIeEFwPSMSX7YOttao8vLQ8YFs6B+2Rg+w0dVeudSJKhfNiLjglnQ5XV6Cg0CLS2x96+dQgArgRp6CnJgI8D40uqK7h8gnfgCyIbo2qn8GPaEtJkMxdfOReayxWF9+JtBfluPXvA3A1CRuWwxiq+d2+mkkhwKwv39t+Dx6P61MED2rgQprpMZ19+qze4qh//3UdJbTuBPukfhrc2adCXlLQAwQ2sHhI98k+wtUENRePFxgOv10BUWgQmdN/Mt9T/hg1+MAO9n/PlRNHEh7BCK2auhy6lygpTx5prCmD9jn/gCSHsU+2syJ95A+QUAPtTaJSKfPvk46m+9LU4jgM5oA2BEWuG74LpBz5vX583RWkRLwncBIKDgbJ7OGFsP4K/a7ERj75ZvsPPu2yCO6ckwfg5AjQfiBNdaTI6YN8MkvgAA8IyDLdVNAD7VZCcMrt2N+PyPt4fjPvzwCaLuwwDIAO0H+MngupMBIg7Q5VrLaEkKARwYUDPGPACmA1irNTne7P/+O9Tecj38H9WCF/SPMQB0DKgJIAeEzIeQZlwLneGSZjDxViLlTq1ptCSHADrAGHMzxmYDuBzAZ+FX4vhAigLXnt348vlnYZ16Kvwb1kMY0j/On55hAJoBagbX3wy98TPoc+dIXFf6JFR5nLmm8MlKa2zfCkBSOIHH+GAEEZ0C4BQA/TusEg6oCmXv3hi6OujGSIINqvpDRCsx/+Qwqgo5FITf6YT73z/A8c5qyFvbII7OA4T0OL75DIAXIB+Y8CuIhj9ATJ8I8Iy/g5SF8ZoKjvlpJIoAOuNZ2Cbl5uqWs3zvFLnxX1xWHwHhG61Zt2AAmAHgpblgYkYcKx4AFIDsABsEMWsJxCwTmJD/A0hdZK4pqNZad4eUEoDFZB8BJt4HCl2hBL6F1LYaJL0envNHcZwrqYeg8ClwPONe6LKrwHUDnQAeITW0ojtN/ZFIOh+gM6orbDmWqe77wPhGNbTziqDrMYRcpkjl94ucG53IlX+on2e6a6Ev+BfS8m5RuW7Q8yBlvHl9/sM9UflIBQFYpjqvZly/iWT74lDr64ag4yyogYcAVtyN5Vi9BQvvK6EmMH4edLnVSDcug5B+ah3AzzWvz5vTnVm+aEhaAVhMjrMsU921UP2vyD5rWdBxHRTfLeFFQ6xfd3q3XoLCwzqEIGStRJrxBYhZFfVgGb81r88rN9cYe2W+Iw4C6N03zGKyD7ZMda8G1H8pgS1TAo6FkForQepHkYqPpyfeE7BwP0828PR7kGb8FPrcK7xMNN5PamiCuabgVW2JniTm1yTsBO57dnhwDFgPPHIGQGIXY7t+FUIsZ6Iqt36t0xnuAjBflfYUSG3roPrvjRj31Jx7PGEAbACpYLoroMueCyF9LMD0r4PkJeaawrgsI+0qMQug2uS4UST/0zlqfaT6Y77VESCo0MEjlEGF+CBjwjRS3ONkXw1k330A7QZYIdD5WpEEggEIAuQC+BkQs++EmHk2GDd8DlIXmGsKrNoSvUnMtWYx2c4n8N+r0PVkDFYVEMoBhColuAVS6/0gxQqwrMhejHi3O/GGALIBDBAyHoMuezqYWLwHhPsVxfP8ZXVD4jllGBMxC6A3sUx1VSvBH80hx2SAFcR9ziH+hGP2AMDTbocu+0pw/bAAmPAkkfRQZU2RQ1vieJEcAjDZTwbYV6HWlzOU9tsjzl4ivv0svHCJgmDiLIjZN0LMGAew9LdA8iJzTeF32hLHm6QQAABYprofJtk2P2C/GqANkZm9RIEhvH3FAfDRELPugZg5BUzI/RqkLjTXFLyrLZEoxGEY2DuQKj3MxOJGMfu/IjtuEki7B8K0GQ8izVgNneFSGxNyblMV/y8TufKRWE/x2FhMruuJfKuDjvkg6a/HefjHADQBBHD9jRAN/wFBP1IGE1eBpOXmmqL92hKJSFIJYM15P3FRX/ix4t80OeSqAFjRcWjEWHhNHrWBCRdCNNwKMf0MgGf8A6QsMNcYN2pLJDJJJQCET94oB2Rr0PXfUAMP9LJDqALUArBSiFn3RcK0BT9GwrQJt0opGpJOAAg7hK+qoYargo7zIind3h9xDDoM69KXQGeoAtcNdAHsT6SGHu+pSF1vkJwCMNnLwPimUOsbOYrv5h5sBQ7180x3DXSG6yCkjSEw3Usg+T5zTeEubYlkIykFgPDk0BJSnPcG7deD1LpjHRXURRgAP0CtgHAOdNm3Q8yYBPCsjyL9/MfaEslK0gqgusJmYFy/SfbVDpdazXEcERyYvhUgZD4OXdZFYGLRDpB6n7mm4GWtdbLT2y503Ki0FntB6hIx45dg+usPLqWKnY5h2v+HNOMG6HOvbGNi4bJImDblKh/J3AIcwDLVXaMEvq0IOc+NMTrIALQApICJl0NnmAsh/TSA6d8EyYvNNYXbtCVSieQXgMkxCVA/Cbqf5qp/cRccQhb+Ghw5AT4BYvZdEDPPAeOGLyP9/HptiVQk6QWAcCvwrCrtnhu0zwgvuojmCMFIlyFk/hm67EvAxJK9ICxVlLbVl9UN6vzUhxQkNQRgahkEJm6WPNVGue36o7QCHcO0/wld9lXg+rIAmPAUqdKDldYiu7ZEqpMSAkB4WHgXKe5HgvZbQMp7mlEBA+AGKAAmXgox+yaIGeMBlv52ZJfNtx2MTyhSRgDVFU0ZjKdvkNs/OUVyT48IgHUI046EmPXHSJg2b0skTPuO9j4nGikjAITjBGZQsDroXAY1tPJgupCxHGL2LHBdaQuAB0kNPlVp7Rf8WeETlJQSAMIO4btK8MeLQ45JYPq50BmugaAfJYOJz4GkZeaaon3aMicyqScAk2McIH+hBH/Sc/1QMJ71YWRYt0Fr20eKYjHZn7BMdTVYTM5fa/P6OAGorrAZqitsnR/g10cfffTRRx999NFHH330cULz/wFv2EqOwnrgagAAAABJRU5ErkJggg=="></img>
                <h1>iDownload-localweb</h1>
                <p>Video URL:</p>
                <input type="text" class="url-input"><br>
                <p></p>
                <div class="start-button-flexbox-container">
                    <div></div>
                    <button type="button" onclick="startYTDownload()" class="-yt">YouTube Download</button>
                    <div></div>
                </div>
                <p></p>
                <div class="start-button-flexbox-container">
                    <div></div>
                    <button type="button" onclick="startBBCDownload()" class="bbc">iPlayer Download</button>
                    <div></div>
                </div>
                <p></p>
                <p class="download-status-text"></p>
                <p></p>
                <div class="finish-button-flexbox-container">
                    <div></div>
                    <button type="button" onclick="location.href='/finishedFile';">Finish Download!</button>
                    <div></div>
                </div>
            </div>
            <div></div>
        </div>
    </body>
</html>
"""

def downloadYTVideo(video, quality):
    global isDownloading, finalFile

    finalFile = ""

    res = "bestvideo[height<=" + str(quality) + "][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    ydl_opts = {
        'logger': Logger(),
        'progress_hooks': [Phook],
        'format': res,
        'merge_output_format' : 'mp4',
        'extractor-args': 'youtube:player-client=default,mweb',
        'cookiefile': 'cookies.txt',
        }
    isDownloading = True
    url = ["https://www.youtube.com/watch?v=", video]
    url = ["".join(url)]
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)

    isDownloading = False
    if message.endswith("has already been downloaded"):
        finalFile = message.replace("[download] ", "").replace(" has already been downloaded", "").strip()
    else:
        finalFile = str(message.replace("Deleting original file ", "").split(".")[0]) + ".mp4".strip()
    print(finalFile)

def downloadBBCVideo(bbcurl, quality):
    global message, isDownloading, finalFile

    currentEpisodeName = ""
    isDownloading = True
    finalFile = ""

    if quality == 1080:
            tvquality = "fhd"
    elif quality == 720:
            tvquality = "hd"
    elif quality == 480:
            tvquality = "sd"
    else:
        tvquality = "fhd"

    cmd = "/usr/local/bin/get_iplayer " + bbcurl + " --tvquality " + tvquality + " --force " + f"--output {script_dir}/"
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, text=True, shell=True)

    for line in p.stdout:
        message = line
        if message.startswith("INFO: Processing tv: "):
            currentEpisodeName = message.replace("INFO: Processing tv: ", "").replace("'", "").replace("(", "").replace(")", "").replace(":", "")
        if "Tagging MP4" in message or "Skipping all versions" in message:
            time.sleep(2)
            isDownloading = False

            message = "INFO: Fetching file prefix"
            
            cmd = '/usr/local/bin/get_iplayer --url="' + bbcurl + '" --info'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=1, text=True, shell=True)
            for line in p.stdout:
                print(line)
                if "fileprefix:" in line:
                    filePrefix = line.replace("fileprefix:      ", "").replace("\n", "")

            finalFile = filePrefix + ".mp4"
            print(finalFile)

app = Flask(__name__)

@app.route("/")
def indexPage():
    return homepage

@app.route("/ytdownload/<video>/<quality>")
def ytdownload(video, quality):
    downloadThread = threading.Thread(target=downloadYTVideo, args=(video,quality,))
    downloadThread.start()
    return "DownloadStarted"

@app.route("/bbcdownload/<url>/<quality>")
def bbcdownload(url, quality):
    url = url.replace("~", "/")
    bbcDownloadThread = threading.Thread(target=downloadBBCVideo, args=(url,quality,))
    bbcDownloadThread.start()
    return "DownloadStarted"

@app.route("/status")
def statusReport():
    if isDownloading:
        try:
            print(f"Sent status: {message}")
            return message
        except:
            print("message not yet defined")
            return ""
    else:
        if finalFile == "":
            return ""
        else:
            return "Ready to download!"
        
@app.route("/finishedFile")
def finishedFileLink():
    return send_file(finalFile, as_attachment=True)
