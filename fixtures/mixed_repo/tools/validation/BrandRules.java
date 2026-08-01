/* BrandRules.java  v001  221108  jrt  */
/*
 Name:        BrandRules.java
 Description: per-brand operational constraints applied before dispatch
*/
package tools.validation;

public class BrandRules {
    public static boolean checkBrandConstraints(String mti) {
        return mti != null && mti.startsWith("01");
    }
}
