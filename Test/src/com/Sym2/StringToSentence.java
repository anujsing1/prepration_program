package com.Sym2;

public class StringToSentence {

	public static void main(String[] args) {
		String[] sentences = "this is a SENTENCE. AND anoTher.".split(".");
		String sentence = convertSentence("this is a SENTENCE. AND anoTher.");
		System.out.println(sentence);
	}
	
	//Convert a string to sentence case
	//e.g.
	//this is a SENTENCE. AND anoTher.
	//This is a sentence. And another.

	public static String convertSentence(String str){
	    String[] sentences = str.split("\\.");
	    String newStr="";
	    for(String sent:sentences){
	        if(sent.length()>1){
	            sent.replace(".","");
	            sent = sent.toLowerCase();
	            char firstLetter = sent.charAt(0);
	            String first = String.valueOf(firstLetter);
	            String subString = sent.substring(1);
	            if(first.equalsIgnoreCase(" ")){
	                firstLetter = sent.charAt(1);
	                first = String.valueOf(firstLetter);
	                subString = sent.substring(2);
	            }
	            first = first.toUpperCase();
	            newStr = newStr + " " + first + subString +".";
	        }
	    }
	    return newStr;
	}
	
}
