package com.programming.array;

public class Lexico {

	public static void main(String[] args) {
		String str = "baabccd";
		StringBuilder a = new StringBuilder(str);
		StringBuilder b = new StringBuilder();
		StringBuilder temp;
		
		for(int i=1; i<=a.length(); i ++)
		{
			if (i==a.length())
			{
				b.append(a.charAt(0));
			}
			else
			{
				b.append(a.charAt(i));
			}
		}
		int result = compare(a, b);
		if (result == -1)
		{
			temp = a;
		}
		else if (result == 1)
		{
			temp = b;
		}
		else
		{
			temp = a;
		}
		a = b;
		
	}
	
	 public static int compare(StringBuilder s1, StringBuilder s2) {
	       for (int i = 0; i < Math.min(s1.length(), s2.length()); i++) {
	           char c1 = s1.charAt(i);
	           char c2 = s2.charAt(i);

	           if (c1 > c2) {
	               return 1;
	           } else if (c2 > c1) {
	               return -1;
	           }
	       }

	       if (s2.length() > s1.length()) {
	           return -1;
	       } else if (s1.length() > s2.length()){
	           return 1;
	       } else {
	           return 0;
	       }
	   }

	 int lexicographic_first(String a, String b)
	 {
	  int ai = 0, bi = 0;

	  /* find the first difference between a and b, unless we run out of characters in one of the strings */
	  while (ai < a.length() && bi < b.length() && a.charAt(ai++) == b.charAt(bi++))
	    ;

	  if (ai == a.length() && bi == b.length()) /* we ran out of characters in both strings */
	    return 0; /* strings are equal */
	  if (ai == a.length()) /* we ran out of characters in a */
	    return -1; /* a came first */
	  if (bi == b.length()) /* we ran out of characters in b */
	    return 1; /* b came first */

	  if (a.charAt(ai) < b.charAt(bi))    /* we're now looking at the first difference between a and b */
	    return -1; /* a came first */
	  return 1; /* b came first */
	 }
}
