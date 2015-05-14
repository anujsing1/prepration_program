/**
 * 
 */
package com.crest;

import java.util.ArrayList;
import java.util.Scanner;


/**
 * @author govind.gupta
 *
 */
public class FinalDrawShape {
	
	public static Shape shape;
	public static ArrayList<Shape> shapes;
	public static int cWidth;
	public static int cHeight;
	public static boolean quit = false;
	static StringBuilder canvas = null;

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		int x1=0, y1=0, x2=0, y2=0;
		Character cmd = null;
		shapes = new ArrayList<Shape>();

        do
        {
        	System.out.println("Please enter a command: ");
   	     
            Scanner inputCmd = new Scanner(System.in);
           
            //Getting input in String format
            String command = inputCmd.nextLine();
            String[] inputs = command.split(" ");
            System.out.println("Command Entered " + command);
            if (inputs.length >= 1)
            {
            	cmd = inputs[0].charAt(0);
            }
        	if (inputs.length >= 3)
        	{
	        	x1 = Integer.parseInt(inputs[1]);
	        	y1 = Integer.parseInt(inputs[2]);
        	}
        	if (inputs.length == 5)
        	{
	        	x2 = Integer.parseInt(inputs[3]);
	        	y2 = Integer.parseInt(inputs[4]);
        	}
        	drawShape(cmd, x1, y1, x2, y2);
        }while(!quit);
	}
	
	private static void drawShape(Character cmd, int x1, int y1, int x2, int y2) {
		if ('Q' == Character.toUpperCase(cmd))
		{
			quit = true;
			System.out.println("System Exit!");
		}
		else
		{
			if('C' == Character.toUpperCase(cmd))
			{
				cWidth = x1;
				cHeight = y1;
//				createCanvas();
				createCanvasString();
				System.out.println();
			}
			else if ('L' == Character.toUpperCase(cmd) || 'R' == Character.toUpperCase(cmd))
			{
				shape = new Shape(Character.toUpperCase(cmd), x1, y1, x2, y2);
				shapes.add(shape);
//				createCanvas();
				createCanvasString();
				System.out.println();
			}
		}
	}

	public static void createCanvas()
	{
		StringBuilder hLine = createHorizontalLine(cWidth, '-');
		System.out.print(hLine);
		System.out.println();
		
		for(int i=0;i<cHeight;i++)
		{
			System.out.print("|");
			for(int j=0;j<cWidth-2;j++)
			{
				for (Shape s : shapes)
				{
					int x1 = s.getX1(), y1 = s.getY1(), x2 = s.getX2(), y2 = s.getY2();
					if (s.getCmd() == 'L')
					{
						drawLine(i, j, x1, y1, x2, y2);
					}
					else if (s.getCmd() == 'R')
					{
						drawRectangle(i, j, x1, y1, x2, y2);
					}
				}
				System.out.print(" ");
			}
			System.out.println("|");
		}
		System.out.print(hLine);
	}
	
	public static void createCanvasString()
	{
		canvas = new StringBuilder();
		StringBuilder hLine = createHorizontalLine(cWidth, '-');
		canvas.append(hLine);
		canvas.append("\n");
		
		for(int i=0;i<cHeight;i++)
		{
//			System.out.print("|");
			canvas.append("|");
			for(int j=0;j<cWidth-2;j++)
			{
				for (Shape s : shapes)
				{
					int x1 = s.getX1(), y1 = s.getY1(), x2 = s.getX2(), y2 = s.getY2();
					if (s.getCmd() == 'L')
					{
						drawLine(i, j, x1, y1, x2, y2);
					}
					else if (s.getCmd() == 'R')
					{
						drawRectangle(i, j, x1, y1, x2, y2);
					}
				}
//				System.out.print(" ");
				canvas.append(" ");
			}
//			System.out.println("|");
			canvas.append("|");
			canvas.append("\n");
		}
//		System.out.print(hLine);
		canvas.append(hLine);
		fillColor(2,2);
		System.out.println(canvas);
	}
	
	public static void fillColorAgain(int x, int y)
	{
		StringBuilder filledCanvas = new StringBuilder();
		char color = 'z';
		String[] rows = canvas.toString().split("\n");
		filledCanvas.append(rows[0]);
		filledCanvas.append("\n");
		char[] column = rows[y].toCharArray();
		for(int i=x-1; column[i] != 'x'; i--)
		{
			column[i] = color;
			
		}
	
		filledCanvas.append(rows[rows.length-1]);
		System.out.println(filledCanvas);
//		String row = rows[y-1];
	}
	
	public static void fillColor(int x, int y)
	{
		StringBuilder filledCanvas = new StringBuilder();
		char color = 'z';
		String[] rows = canvas.toString().split("\n");
		filledCanvas.append(rows[0]);
		filledCanvas.append("\n");
		for (int k=y-1;rows[k].toCharArray()[x-1] != 'x' && /*rows[k].toCharArray()[x-1] != '-'*/ k > 0 /*&& rows[k].toCharArray()[x-1] != '|'*/; k--)
		{
			char[] columns = rows[k].toCharArray();
			for (int i=x-1; columns[i] != 'x' && /*columns[i] != '|'*/ i > 0 /*&& columns[i] != '-'*/; i--)
			{
				columns[i] = color;
			}
			
			for (int i=x; columns[i] != 'x' && /*columns[i] != '|'*/ i < cWidth-2 /*&& columns[i] != '-'*/; i++)
			{
				columns[i] = color;
			}
			filledCanvas.append(columns);
			filledCanvas.append("\n");
		}
		
		for (int k=y;rows[k].toCharArray()[x-1] != 'x' && /*rows[k].toCharArray()[x-1] != '-'*/ k <= cHeight /*&& rows[k].toCharArray()[x-1] != '|'*/; k++)
		{
			char[] columns = rows[k].toCharArray();
			for (int i=x-1; columns[i] != 'x' && /*columns[i] != '|'*/ i>0 /*&& columns[i] != '-'*/; i--)
			{
				columns[i] = color;
			}
			
			for (int i=x; columns[i] != 'x' && /*columns[i] != '|'*/i < cWidth-2 /*&& columns[i] != '-'*/; i++)
			{
				columns[i] = color;
			}
			filledCanvas.append(columns);
			filledCanvas.append("\n");
		}
		filledCanvas.append(rows[rows.length-1]);
		System.out.println(filledCanvas);
		String row = rows[y-1];
	}
	
	public static void drawRectangle(int i, int j, int x1, int y1, int x2, int y2)
	{
		StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
		if (i+1 == y1 || i+1 == y2)
		{
			if (j+1 == x1)
				System.out.print(lineToDraw);
		}
		else if (i+1 < y2 && i+1 > y1)
		{
			if(j+1 == x2-2 || j+1 == x1)
			{
				System.out.print('x');
			}
		}
	}
	
	public static void drawLine(int i, int j, int x1, int y1, int x2, int y2)
	{
		if (y1 == y2)
		{
			drawHLine(i, j, x1, y1, x2, y2);
		}
		else if (x1==x2)
		{
			drawVLine(i, j, x1, y1, x2, y2);
		}
	}
	
	public static void drawVLine(int i, int j, int x1, int y1, int x2, int y2)
	{
		if (i+1 >= y1 && i+1 <= y2)
		{
			if (x1 == j+1)
//				System.out.print('x');
				canvas.append("x");
		}
	}
	
	public static void drawHLine(int i, int j, int x1, int y1, int x2, int y2)
	{
		StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
		if (i+1 == y1)
		{
			if (x1 == j+1)
			{
//				System.out.print(lineToDraw);
				canvas.append(lineToDraw);
			}
		}
	}
	
	public static StringBuilder createHorizontalLine(int width, char c)
	{
		StringBuilder verticalLine = new StringBuilder();
		for (int i=0;i<width;i++)
		{
			verticalLine = verticalLine.append(c);
		}
		return verticalLine;
	}
}
